import pytest
from unittest.mock import Mock, AsyncMock, patch
from aiogram.types import Message

from bot.handlers.manager.create_cargo import create_cargo_router
from bot.handlers.manager.manage_cargo import manage_cargo_router
from bot.handlers.manager.update_status import update_status_router
from bot.handlers.manager.view_cargos import view_cargos_router
from bot.handlers.manager.export import export_router
from bot.utils.notifications import send_status_notification
from database.crud import ClientCRUD, ShipmentCRUD
from database.models import Client, Shipment, CargoStatus

# Mock bot
@pytest.fixture
async def mock_bot():
    """Bot mock yaratish"""
    bot = Mock(spec=Mock)

    # Mock i18n middleware
    bot.middleware = Mock(spec=Mock)
    bot.middleware.get_text = lambda lang, key, **kw: key.format(**kw)

    # Mock send_message
    bot.send_message = AsyncMock(return_value=None)
    bot.send_message.side_effect = lambda chat_id, text, **kw: Mock()

    return bot


# Test Manager router integration
@pytest.mark.asyncio
async def test_manager_create_cargo_router_exists():
    """Create cargo router tekshirish"""
    assert create_cargo_router is not None
    assert callable(create_cargo_router)


@pytest.mark.asyncio
async def test_manager_manage_cargo_router_exists():
    """Manage cargo router tekshirish"""
    assert manage_cargo_router is not None
    assert callable(manage_cargo_router)


@pytest.mark.asyncio
async def test_manager_update_status_router_exists():
    """Update status router tekshirish"""
    assert update_status_router is not None
    assert callable(update_status_router)


@pytest.mark.asyncio
async def test_manager_view_cargos_router_exists():
    """View cargos router tekshirish"""
    assert view_cargos_router is not None
    assert callable(view_cargos_router)


@pytest.mark.asyncio
async def test_manager_export_router_exists():
    """Export router tekshirish"""
    assert export_router is not None
    assert callable(export_router)


# Test: Client flow - Phone input → ID generation
@pytest.mark.asyncio
async def test_client_phone_input_and_id_generation():
    """
    Client flow: Phone input → ID generation
    """
    mock_bot = Mock()
    mock_bot.middleware = Mock(spec=Mock)
    mock_bot.middleware.get_text = lambda lang, key, **kw: key.format(**kw)

    # Import generate_unique_id
    with patch("bot.utils.cargo_id_gen.cargo_id_generator.generate_unique_id") as mock_gen:
        # Mock generate_unique_id to return random string
        mock_gen.cargo_id_counter = 0
        mock_gen.generate_unique_id = AsyncMock(return_value="48392")

        # Simulate flow
        phone = "+9989012345"
        new_cargo_id = await mock_gen.generate_unique_id(None)

        # Verify
        assert new_cargo_id == "48392"
        assert mock_gen.cargo_id_counter == 1


# Test: Shipment attachment → Status update
@pytest.mark.asyncio
async def test_shipment_status_update_with_notification():
    """
    Shipment status update with notification
    """
    mock_bot = Mock()
    mock_bot.middleware = Mock(spec=Mock)
    mock_bot.middleware.get_text = lambda lang, key, **kw: key.format(**kw)
    mock_bot.send_message = AsyncMock(return_value=None)

    # Import send_status_notification
    with patch("bot.utils.notifications.send_status_notification") as mock_notification:
        mock_notification.call_count = 0

        # Simulate status update
        client = Mock(spec=Client)
        client.cargo_id = "48392"
        client.phone_number = "+9989012345"
        client.full_name = "Test Client"
        client.telegram_id = 987654321
        client.language = "uz"

        shipment = Mock(spec=Shipment)
        shipment.id = 1
        shipment.description = "Test Shipment"
        shipment.status = CargoStatus.PENDING

        # Call notification
        await mock_notification(None, 987654321, client, shipment, CargoStatus.READY, "uz")

        # Verify notification was called
        assert mock_notification.call_count == 1
        assert mock_bot.send_message.call_count == 1

        # Verify message content
        assert mock_bot.send_message.call_count == 1
        args = mock_bot.send_message.call_args[0]
        assert args[0][0] == 987654321
        assert "🔔 Xabar" in str(args[0][1])


# Run tests
if __name__ == "__main__":
    pytest.main([__file__], "-v", "-s"])
