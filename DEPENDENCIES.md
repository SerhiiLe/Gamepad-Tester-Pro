# Зависимости Gamepad Tester / System Dependencies

Данный документ содержит перечень библиотек и системных настроек для работы диагностического комплекса Gamepad Tester на различных дистрибутивах Linux.

После миграции графиков на нативный `QPainter` и генерации PDF на `QPdfWriter + QTextDocument` проект больше **не требует** `pyqtgraph`, `numpy`, `reportlab` и `hidapi` — единственной обязательной библиотекой является **`PySide6`**.

---

## 1. Сводная таблица пакетов

| Назначение | Python модуль | Статус | Manjaro / Arch Linux (`pacman`) | Debian / Ubuntu (`apt`) |
| :--- | :--- | :--- | :--- | :--- |
| **GUI, графики и PDF** | `PySide6` | Обязательный | `python-pyside6` | `python3-pyside6` / `pip install PySide6` |
| **Резервное чтение absinfo** | `evdev` | Опциональный fallback | `python-evdev` | `python3-evdev` |

*(Основное чтение устройств `/dev/input/event*` и `/dev/hidraw*` выполняется напрямую через Linux `ioctl` и стандартную библиотеку Python без сторонних обёрток).*

---

## 2. Установка в Manjaro / Arch Linux

```bash
sudo pacman -Syu
sudo pacman -S python-pyside6
```

---

## 3. Установка в Debian / Ubuntu (22.04 / 24.04+)

```bash
sudo apt update
sudo apt install -y python3-pip

# PySide6 (если отсутствует в apt вашего дистрибутива):
pip3 install --user PySide6
```

---

## 4. Установка через Python Virtual Environment (`venv` / `pip`)

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
