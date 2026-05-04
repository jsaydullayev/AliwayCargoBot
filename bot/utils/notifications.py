"""
Notification yuborish funksiyalari
TZ §8 — Status o'zgarganda clientga avtomatik xabar yuborish
"""
import logging
from typing import Any, Optional

from aiogram import Bot
from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest

from database.models import CargoStatus, Client, Shipment

logger = logging.getLogger(__name__)


STATUS_KEY_MAP = {
    CargoStatus.PENDING: "status.pending",
    CargoStatus.IN_TRANSIT: "status.in_transit",
    CargoStatus.ARRIVED: "status.arrived",
    CargoStatus.READY: "status.ready",
    CargoStatus.DELIVERED: "status.delivered",
}

STATUS_MESSAGE_KEY_MAP = {
    CargoStatus.PENDING: "notification.status_messages.pending",
    CargoStatus.IN_TRANSIT: "notification.status_messages.in_transit",
    CargoStatus.ARRIVED: "notification.status_messages.arrived",
    CargoStatus.READY: "notification.status_messages.ready",
    CargoStatus.DELIVERED: "notification.status_messages.delivered",
}


async def send_status_notification(
    bot: Bot,
    client: Client,
    shipment: Shipment,
    i18n: Any,
) -> bool:
    """
    Status o'zgarganda clientga notification yuborish

    Args:
        bot: Aiogram Bot instance (handler argumentidan olinadi)
        client: Client obyekti
        shipment: Shipment obyekti (yangilangan status bilan)
        i18n: I18nMiddleware instance

    Returns:
        True — xabar yuborildi, False — yuborilmadi (loglanadi)
    """
    if not client.telegram_id:
        logger.info(f"Client {client.cargo_id} hali botdan foydalanmagan, notification o'tkazib yuborildi")
        return False

    if not i18n:
        logger.warning("i18n middleware mavjud emas, notification yuborib bo'lmaydi")
        return False

    lang = client.language or "uz"

    status_text = i18n.get_text(lang, STATUS_KEY_MAP.get(shipment.status, ""))
    status_message = i18n.get_text(lang, STATUS_MESSAGE_KEY_MAP.get(shipment.status, ""))

    notification_text = i18n.get_text(
        lang,
        "notification.status_updated",
        cargo_id=client.cargo_id or "—",
        description=shipment.description or "—",
        status=status_text,
        message=status_message,
    )

    try:
        await bot.send_message(
            chat_id=client.telegram_id,
            text=notification_text,
        )
        logger.info(f"Notification yuborildi — User: {client.telegram_id}, Cargo: {client.cargo_id}")
        return True
    except TelegramForbiddenError:
        logger.warning(f"Client {client.telegram_id} botni bloklagan")
        return False
    except TelegramBadRequest as e:
        logger.warning(f"Notification yuborib bo'lmadi (User: {client.telegram_id}): {e}")
        return False
    except Exception as e:
        logger.error(f"Kutilmagan xato (User: {client.telegram_id}): {e}", exc_info=True)
        return False


async def send_cargo_id_notification(
    bot: Bot,
    client: Client,
    new_cargo_id: str,
    i18n: Any,
    old_cargo_id: Optional[str] = None,
) -> bool:
    """
    Yangi yoki yangilangan Cargo ID haqida clientga xabar

    Args:
        bot: Aiogram Bot instance
        client: Client obyekti
        new_cargo_id: Yangi Cargo ID
        i18n: I18nMiddleware instance
        old_cargo_id: Eski Cargo ID (agar yangilanish bo'lsa)

    Returns:
        True — xabar yuborildi, False — yuborilmadi
    """
    if not client.telegram_id:
        return False

    if not i18n:
        return False

    lang = client.language or "uz"

    if old_cargo_id:
        text = i18n.get_text(
            lang,
            "notification.cargo_id_updated",
            old_id=old_cargo_id,
            new_id=new_cargo_id,
        )
    else:
        text = i18n.get_text(
            lang,
            "notification.cargo_id_assigned",
            cargo_id=new_cargo_id,
        )

    try:
        await bot.send_message(chat_id=client.telegram_id, text=text)
        logger.info(f"Cargo ID notification yuborildi — User: {client.telegram_id}")
        return True
    except (TelegramForbiddenError, TelegramBadRequest) as e:
        logger.warning(f"Cargo ID notification yuborib bo'lmadi: {e}")
        return False
    except Exception as e:
        logger.error(f"Kutilmagan xato: {e}", exc_info=True)
        return False
