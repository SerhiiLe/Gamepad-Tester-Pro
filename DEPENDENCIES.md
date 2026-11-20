# Зависимости Gamepad Tester / System Dependencies

Данный документ содержит перечень необходимых библиотек и системных пакетов для работы диагностического комплекса Gamepad Tester на различных дистрибутивах Linux.

---

## 1. Сводная таблица пакетов

| Назначение | Python модуль | Manjaro / Arch Linux (`pacman`) | Debian / Ubuntu (`apt`) |
| :--- | :--- | :--- | :--- |
| **Графический интерфейс** | `PySide6` | `python-pyside6` | `python3-pyside6` / `pip install PySide6` |
| **Аппаратные 2D-графики** | `pyqtgraph` | `python-pyqtgraph` | `python3-pyqtgraph` / `pip install pyqtgraph` |
| **Низкоуровневый ввод** | `evdev` | `python-evdev` | `python3-evdev` |
| **Прямой доступ к HID** | `hid` (hidapi) | `python-hidapi` | `python3-hid` / `pip install hidapi` |
| **Генерация PDF-отчетов** | `reportlab` | `python-reportlab` | `python3-reportlab` |
| **NumPy (математика)** | `numpy` | `python-numpy` | `python3-numpy` |

---

## 2. Установка в Manjaro / Arch Linux

В Manjaro все необходимые библиотеки доступны в официальных репозиториях:

```bash
sudo pacman -Syu
sudo pacman -S python-pyside6 python-pyqtgraph python-evdev python-hidapi python-reportlab python-numpy
```

---

## 3. Установка в Debian / Ubuntu (22.04 / 24.04+)

В Debian и Ubuntu большинство пакетов доступно через `apt`:

```bash
sudo apt update
sudo apt install -y python3-evdev python3-reportlab python3-numpy python3-pip libhidapi-dev

# PySide6 и pyqtgraph (если отсутствуют в apt дистрибутива):
pip3 install --user PySide6 pyqtgraph hidapi
```

---

## 4. Установка через Python Virtual Environment (`venv` / `pip`)

Если вы предпочитаете изолированное виртуальное окружение:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

## 5. Настройка прав доступа к устройствам (Udev Rules)

По умолчанию устройства `/dev/input/event*` и `/dev/hidraw*` в некоторых дистрибутивах могут требовать прав суперпользователя. Чтобы запускать утилиту без `sudo`:

### Способ 1: Добавление пользователя в группу `input`
```bash
sudo usermod -a -G input $USER
```
*(После выполнения требуется перелогиниться).*

### Способ 2: Создание udev-правила для геймпадов (рекомендуется)
Создайте файл `/etc/udev/rules.d/99-gamepad.rules`:
```udev
# Доступ к hidraw и event для игровых контроллеров
KERNEL=="hidraw*", ATTRS{idVendor}=="054c", MODE="0666"   # Sony DualShock / DualSense
KERNEL=="hidraw*", ATTRS{idVendor}=="045e", MODE="0666"   # Microsoft Xbox
KERNEL=="hidraw*", ATTRS{idVendor}=="2e8a", MODE="0666"   # Raspberry Pi Pico / GP2040-CE
KERNEL=="uinput", MODE="0660", GROUP="input", OPTIONS+="static_node=uinput"
```
Примените правила:
```bash
sudo udevadm control --reload-rules && sudo udevadm trigger
```

