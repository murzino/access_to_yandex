from django.shortcuts import render
from django.http import HttpResponse
import requests
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt


# Функция для отображения файлов и папок
def list_files(request):
    public_key = request.GET.get('public_key', '')
    path = request.GET.get('path', '')  # Получаем путь, если указан

    if not public_key:
        return render(request, 'list_files.html', {'error': 'Введите публичную ссылку.'})

    url = 'https://cloud-api.yandex.net/v1/disk/public/resources'
    params = {'public_key': public_key, 'path': path}
    response = requests.get(url, params=params)

    if response.status_code == 200:
        data = response.json()
        items = data.get('_embedded', {}).get('items', [])

        # Проверка на корень папки
        current_path = data.get('path', '')  # Текущий путь
        if current_path != '/': 
            parent_path = current_path.rsplit('/', 1)[0]
        else:
            parent_path = None

        context = {
            'files': items,
            'public_key': public_key,
            'current_path': path,
            'parent_path': parent_path if path else None, 
        }

        return render(request, 'list_files.html', context)
    else:
        return render(request, 'list_files.html', {'error': 'Не удалось получить список файлов.'})

# Функция для загрузки папок с Яндекс.Диска
@csrf_exempt
def download_file(request):
    if request.method == 'POST':
        file_url = request.POST.get('file_url')
        file_name = request.POST.get('file_name')

        if not file_url or not file_name:
            return HttpResponse('Некорректный запрос.', status=400)

        response = requests.get(file_url, stream=True)

        if response.status_code == 200:
            response_content = HttpResponse(response.content, content_type='application/octet-stream')
            response_content['Content-Disposition'] = f'attachment; filename="{file_name}"'
            return response_content
        else:
            return HttpResponse('Не удалось скачать файл.', status=500)

    return HttpResponse('Метод не поддерживается.', status=405)


@csrf_exempt
def download_folder_as_zip(request):
    if request.method == 'POST':
        public_key = request.POST.get('public_key')
        folder_path = request.POST.get('folder_path')

        if not public_key or not folder_path:
            return HttpResponse('Некорректный запрос.', status=400)

        url = 'https://cloud-api.yandex.net/v1/disk/public/resources/download'
        params = {'public_key': public_key, 'path': folder_path}
        response = requests.get(url, params=params)

        if response.status_code == 200:
            download_link = response.json().get('href')
            if download_link:
                archive_response = requests.get(download_link, stream=True)
                if archive_response.status_code == 200:
                    response_content = HttpResponse(archive_response.content, content_type='application/zip')
                    response_content['Content-Disposition'] = f'attachment; filename="{folder_path.split("/")[-1]}.zip"'
                    return response_content
                else:
                    return HttpResponse('Не удалось скачать архив.', status=500)
            else:
                return HttpResponse('Ссылка для скачивания не найдена.', status=500)
        else:
            return HttpResponse('Не удалось создать ссылку на архив.', status=500)

    return HttpResponse('Метод не поддерживается.', status=405)