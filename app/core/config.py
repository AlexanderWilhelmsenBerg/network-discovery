from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_name: str = Field(default="Homelab Control Service", alias="APP_NAME")
    app_host: str = Field(default="0.0.0.0", alias="APP_HOST")
    app_port: int = Field(default=8100, alias="APP_PORT")
    app_base_url: str = Field(default="http://localhost:8100", alias="APP_BASE_URL")
    secret_key: str = Field(default="change-me", alias="SECRET_KEY")

    mariadb_host: str = Field(default="mariadb.lab", alias="MARIADB_HOST")
    mariadb_port: int = Field(default=3306, alias="MARIADB_PORT")
    mariadb_db: str = Field(default="homelab_control", alias="MARIADB_DB")
    mariadb_user: str = Field(default="discovery", alias="MARIADB_USER")
    mariadb_password: str = Field(default="change-me", alias="MARIADB_PASSWORD")

    redis_host: str = Field(default="redis2.lab", alias="REDIS_HOST")
    redis_port: int = Field(default=6379, alias="REDIS_PORT")
    redis_db: int = Field(default=0, alias="REDIS_DB")

    unifi_api_url: str = Field(default="https://unifi.lab", alias="UNIFI_API_URL")
    unifi_username: str | None = Field(default=None, alias="UNIFI_USERNAME")
    unifi_password: str | None = Field(default=None, alias="UNIFI_PASSWORD")
    unifi_site: str = Field(default="default", alias="UNIFI_SITE")
    unifi_verify_ssl: bool = Field(default=False, alias="UNIFI_VERIFY_SSL")

    opnsense_api_url: str = Field(default="https://opnsense.lab", alias="OPNSENSE_API_URL")
    opnsense_api_key: str | None = Field(default=None, alias="OPNSENSE_API_KEY")
    opnsense_api_secret: str | None = Field(default=None, alias="OPNSENSE_API_SECRET")
    opnsense_verify_ssl: bool = Field(default=False, alias="OPNSENSE_VERIFY_SSL")

    proxmox_ssh_host: str = Field(default="proxmox.lab", alias="PROXMOX_SSH_HOST")
    proxmox_ssh_user: str = Field(default="root", alias="PROXMOX_SSH_USER")
    proxmox_ssh_key_path: str = Field(default="/root/.ssh/id_rsa", alias="PROXMOX_SSH_KEY_PATH")

    discovery_poll_seconds: int = Field(default=900, alias="DISCOVERY_POLL_SECONDS")
    default_homelab_vlan_id: int | None = Field(default=None, alias="DEFAULT_HOMELAB_VLAN_ID")
    default_domain: str = Field(default="lab", alias="DEFAULT_DOMAIN")

    @property
    def database_url(self) -> str:
        return (
            f"mysql+pymysql://{self.mariadb_user}:{self.mariadb_password}"
            f"@{self.mariadb_host}:{self.mariadb_port}/{self.mariadb_db}"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
