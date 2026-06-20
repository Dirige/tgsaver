"""首次登录脚本 - 交互式运行：python3 login.py"""
import asyncio
from pyrogram import Client
import yaml
from pathlib import Path

CONFIG_PATH = Path(__file__).parent / "config.yaml"

async def main():
    # Load config
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    proxy = {
        "scheme": cfg["proxy"]["scheme"],
        "hostname": cfg["proxy"]["host"],
        "port": cfg["proxy"]["port"],
    }

    async with Client(
        name="tg_saver",
        api_id=cfg["api_id"],
        api_hash=cfg["api_hash"],
        proxy=proxy,
    ) as client:
        session_string = await client.export_session_string()
        me = await client.get_me()
        print(f"登录成功: {me.first_name}")
        print(f"SESSION_STRING={session_string}")

        # Save session string to config.yaml
        cfg["session_string"] = session_string
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            yaml.dump(cfg, f, allow_unicode=True, default_flow_style=False)
        print(f"已保存到 {CONFIG_PATH}")

if __name__ == "__main__":
    asyncio.run(main())
