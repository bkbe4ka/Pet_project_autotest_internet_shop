import datetime
import os


class Logger:
    # ИСПРАВЛЕНО: относительный путь вместо C:\Users\Глеб\...\logs (падал в CI и у всех других)
    LOG_DIR = os.path.join(os.getcwd(), "logs")
    file_name = os.path.join(
        LOG_DIR, f"log_{datetime.datetime.now():%Y-%m-%d_%H-%M-%S}.log")

    @classmethod
    def write_log_to_file(cls, data: str):
        try:
            os.makedirs(cls.LOG_DIR, exist_ok=True)
            with open(cls.file_name, "a", encoding="utf-8") as f:   # было 'utf=8' (опечатка, хоть и не падала)
                f.write(data)
        except Exception as e:
            # лог не должен ронять тест
            print(f"[logger] не удалось записать лог: {e}")

    @classmethod
    def add_start_step(cls, method: str):
        test_name = os.environ.get("PYTEST_CURRENT_TEST", "manual")
        data = (
            "\n-----\n"
            f"Test: {test_name}\n"
            f"Start time: {datetime.datetime.now()}\n"
            f"Start name method: {method}\n\n"
        )
        cls.write_log_to_file(data)

    @classmethod
    def add_end_step(cls, url: str, method: str):
        data = (
            f"End time: {datetime.datetime.now()}\n"
            f"End name method: {method}\n"
            f"URL: {url}\n"
            "\n-----\n"
        )
        cls.write_log_to_file(data)
