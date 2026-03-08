# Сервіс класифікації зображень (MobileNetV2)

Цей проект реалізує контейнеризований ML-сервіс на Python для класифікації
зображень за допомогою моделі MobileNetV2, експортованої у формат TorchScript.

## Попередні вимоги
* Зображення у форматі JPEG/JPG для тестування.

## Швидкий старт

### 1. Запустити скрипт для установки dev середовища
> ! ПОПЕРЕДЖЕННЯ: Скприпт підтримує тільки **Linux Fedora/Ubuntu**
```bash
chmod u+x install_dev_tools.sh
sudo ./install_dev_tools.sh
```

### 1.2 Якщо скрипт не запускається рекомендовано встановити такі залежності:
- Docker
- Python >= 3.9

Після установки створити віртуальне оточення і встановити необхідні пакети

### 2. Підготовка моделі
Спочатку згенеруйте файл моделі TorchScript:
```bash
python export_model.py
```

### 3. Збірка образів
Виберіть варіант збірки залежно від потреб:

```bash
# Збірка оптимізованого Slim-образу (рекомендовано)
docker build -t ml-service:slim -f Dockerfile.slim .

# Збірка важкого Fat-образу
docker build -t ml-service:fat -f Dockerfile.fat .
```

### 4. Запуск інференсу
Щоб класифікувати зображення, прокиньте локальний файл у контейнер:
```bash
docker run --rm \
  -v "$(pwd)/test_image.jpeg:/app/test_image.jpeg" \
  ml-service:slim test_image.jpeg
```

## Структура проєкту
```
lesson-3/
├── inference.py
├── export_model.py
├── model.pt
├── Dockerfile.fat
├── Dockerfile.slim
├── install_dev_tools.sh
├── report.md
└── README.md
```
