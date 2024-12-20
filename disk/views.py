from django.shortcuts import render
from django.http import HttpResponse
import requests
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from typing import Optional, Dict


# Функция для отображения файлов и папок
def list_files(request) -> HttpResponse:

    public_key = request.GET.get('public_key', '')  # Получаем публичный ключ из GET
    path = request.GET.get('path', '')  

    if not public_key:  # Если отсутствует - выводим ошибку
        return render(request, 'list_files.html', {'error': 'Введите публичную ссылку.'})

    # Отправляем запрос к API Яндекс.Диска для получения списка файлов и папок
    url = 'https://cloud-api.yandex.net/v1/disk/public/resources'
    params = {'public_key': public_key, 'path': path}
    response = requests.get(url, params=params)

    if response.status_code == 200:
        data = response.json()  # 
        items = data.get('_embedded', {}).get('items', [])  # Получаем список файлов и папок

        # Проверка на корень папки и определение родительской папки
        current_path = data.get('path', '')  # Текущий путь
        parent_path = current_path.rsplit('/', 1)[0] if current_path != '/' else None  # Родительский путь

        # Подготовка контекста для передачи данных в шаблон
        context = {
            'files': items,  # Список файлов и папок
            'public_key': public_key,  # Публичный ключ
            'current_path': path,  # Текущий путь
            'parent_path': parent_path if path else None,  # Родительский путь
        }

        return render(request, 'list_files.html', context)
    else:
        return render(request, 'list_files.html', {'error': 'Не удалось получить список файлов.'})


# Функция для загрузки отдельного файла с Яндекс.Диска
@csrf_exempt
def download_file(request) -> HttpResponse:
    if request.method == 'POST':
        file_url = request.POST.get('file_url')  # Получаем URL файла для скачивания
        file_name = request.POST.get('file_name')  # Получаем имя файла

        if not file_url or not file_name:  
            return HttpResponse('Некорректный запрос.', status=400)

        # Отправляем запрос к Яндекс.Диску для получения файла
        response = requests.get(file_url, stream=True)

        if response.status_code == 200:
            response_content = HttpResponse(response.content, content_type='application/octet-stream')
            response_content['Content-Disposition'] = f'attachment; filename="{file_name}"'
            return response_content
        else:
            return HttpResponse('Не удалось скачать файл.', status=500)

    # Если метод не POST, возвращаем ошибку
    return HttpResponse('Метод не поддерживается.', status=405)


# Функция для скачивания папки в формате ZIP с Яндекс.Диска
@csrf_exempt
def download_folder_as_zip(request) -> HttpResponse:

    if request.method == 'POST':
        public_key = request.POST.get('public_key')  # Получаем публичный ключ
        folder_path = request.POST.get('folder_path')  # Получаем путь к папке

        if not public_key or not folder_path:  
            return HttpResponse('Некорректный запрос.', status=400)

        # Запрашиваем ссылку для скачивания архива с Яндекс.Диска
        url = 'https://cloud-api.yandex.net/v1/disk/public/resources/download'
        params = {'public_key': public_key, 'path': folder_path}
        response = requests.get(url, params=params)

        if response.status_code == 200:
            # Получаем ссылку для скачивания архива
            download_link = response.json().get('href')
            if download_link:
                # Запрашиваем сам архив
                archive_response = requests.get(download_link, stream=True)
                if archive_response.status_code == 200:
                    # Отправляем архив клиенту
                    response_content = HttpResponse(archive_response.content, content_type='application/zip')
                    response_content['Content-Disposition'] = f'attachment; filename="{folder_path.split("/")[-1]}.zip"'
                    return response_content
                else:
                    # Если архив не был загружен, выводим ошибку
                    return HttpResponse('Не удалось скачать архив.', status=500)
            else:
                # Если ссылка на архив не найдена, выводим ошибку
                return HttpResponse('Ссылка для скачивания не найдена.', status=500)
        else:
            # Если не удалось создать ссылку для скачивания архива, выводим ошибку
            return HttpResponse('Не удалось создать ссылку на архив.', status=500)

    # Если метод не POST, возвращаем ошибку
    return HttpResponse('Метод не поддерживается.', status=405)
