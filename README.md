# Автотест интернет-магазина (Selenium + pytest + allure) с самовосстановлением selfheal

Тестовый сценарий: с главной Ozon → в каталог → раздел мониторов → фильтрация по нескольким
пунктам → сортировка по рейтингу → карточка товара → в корзину → в избранное → удаление из
корзины → переход в избранное.

Инструменты: pytest, allure, selenium. Локаторы защищены слоем **selfheal** (встроен в проект,
папка `selfheal/`): при поломке хрупких XPATH движок переидентифицирует элемент по устойчивым
признакам и либо чинит на лету, либо предлагает правку человеку.

## Запуск

```bash
pip install -r requirements.txt
playwright_not_needed=true   # selfheal-ядро без браузера; здесь нужен только Chrome для Selenium

# безопасный режим: ловит поломки локаторов и предлагает правки (по умолчанию)
SELFHEAL_MODE=propose pytest Tests/test_choose_monitor.py

# отчёт allure (как раньше)
pytest --alluredir=allure-results Tests/ && allure serve allure-results
```

Режимы `SELFHEAL_MODE`: `propose` (предлагать, по умолчанию) | `inline` (чинить на лету,
когда уверенность высока и действие неразрушающее) | `off` (обычный Selenium без heal).

## Что делать после поломки локатора

```bash
python -m selfheal.cli review     # старый XPATH -> предложенный локатор + уверенность
python -m selfheal.cli report     # сводка прогона
python -m selfheal.cli calibrate  # переобучить калибратор по накопленным исходам
```

Одобрили предложение — впишите новый локатор в соответствующий page-объект и закоммитьте.
Папку `.selfheal/fingerprints/` **коммитьте** (история локаторов, видна в PR); `state.db` и
`*.jsonl` — в `.gitignore`.

## Что изменилось против исходной версии

- Драйвер вынесен в фикстуру `driver` в корневом `conftest.py` **с `driver.quit()`** (раньше
  браузер оставался висеть).
- Переключение вкладок — через `switch_to_new_tab()` вместо хрупких `window_handles[1..3]`.
- `assert_word` теперь действительно роняет тест при несовпадении (раньше ошибка проглатывалась).
- Захардкоженные пути `C:\Users\Глеб\...` в логгере и скриншотах заменены на относительные.
- Все `WebDriverWait(...).until(EC.element_to_be_clickable(...))` заменены на `self.find(xpath,
  intent=..., action=...)` — поиск с самовосстановлением.
- Жёсткие `window.scrollTo(0, N)` заменены на `scroll_to(element)` (scrollIntoView).
- Удаление из корзины помечено `action="destructive"` — никогда не чинится автоматически.
- Исправлен баг копипасты в `cart_page.get_favourite_word` (возвращал не тот локатор).
- `conftest.py` перенесён из `utilities/` в корень (там он был невидим для `Tests/`).
```
