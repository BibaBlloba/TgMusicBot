from aiogram import Bot, Dispatcher
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    TOKEN: str

    @property
    def bot(self) -> Bot:
        return Bot(token=self.TOKEN)

    @property
    def dp(self) -> Dispatcher:
        return Dispatcher()

    model_config = SettingsConfigDict(env_file='.env', extra='ignore')


settings = Settings()
