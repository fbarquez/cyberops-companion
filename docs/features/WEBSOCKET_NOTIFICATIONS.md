# WebSocket Notifications

Real-time notification delivery using WebSocket connections for instant updates without polling.

## Overview

The WebSocket notification system provides:
- Instant notification delivery to connected users
- Real-time stats updates (unread count)
- Connection status indicator
- Automatic reconnection with exponential backoff
- Support for multiple tabs/devices per user

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend                                 │
├─────────────────────────────────────────────────────────────────┤
│  useNotificationWebSocket Hook                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ - Manages WebSocket connection                            │  │
│  │ - Handles reconnection                                    │  │
│  │ - Dispatches events to callbacks                         │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              │                                   │
│                              ▼                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ NotificationBell Component                                │  │
│  │ - Shows unread count badge                               │  │
│  │ - Displays recent notifications dropdown                  │  │
│  │ - Shows toast for new notifications                       │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ WebSocket (wss://)
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                         Backend                                  │
├─────────────────────────────────────────────────────────────────┤
│  NotificationConnectionManager                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ - Tracks active connections per user                      │  │
│  │ - Supports multiple connections (tabs/devices)            │  │
│  │ - Broadcasts messages to user connections                 │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              │                                   │
│                              ▼                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ NotificationService                                       │  │
│  │ - Creates notifications in database                       │  │
│  │ - Triggers WebSocket broadcast                            │  │
│  │ - Sends email/webhook as configured                       │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## WebSocket Endpoint

### Connection

```
ws://localhost:8000/api/v1/ws/notifications?token=<jwt_token>
```

**Authentication:** JWT token passed as query parameter

**Close Codes:**
| Code | Reason |
|------|--------|
| 4001 | Missing authentication token |
| 4002 | Invalid or expired token |
| 4003 | Invalid token payload |
| 1000 | Normal close |

### Events

#### Server → Client

| Event | Description | Data |
|-------|-------------|------|
| `connection:established` | Connection confirmed | `{ user_id, timestamp, message }` |
| `notification:new` | New notification | `NotificationData` |
| `notification:read` | Notification marked read | `{ id }` |
| `notification:deleted` | Notification deleted | `{ id }` |
| `stats:updated` | Stats changed | `NotificationStats` |

#### Client → Server

| Type | Description |
|------|-------------|
| `ping` | Keep-alive ping (server responds with `pong`) |

### Message Format

```typescript
// Server message
{
  "event": "notification:new",
  "data": {
    "id": "uuid",
    "type": "incident_created",
    "priority": "high",
    "title": "New Incident Created",
    "message": "Incident INC-2024-001 has been created",
    "entity_type": "incident",
    "entity_id": "uuid",
    "entity_url": "/incidents/uuid",
    "is_read": false,
    "created_at": "2024-01-31T12:00:00Z"
  },
  "timestamp": "2024-01-31T12:00:00Z"
}

// Client ping
{
  "type": "ping"
}
```

## Backend Implementation

### Files

| File | Description |
|------|-------------|
| `apps/api/src/api/websocket.py` | WebSocket endpoints and managers |
| `apps/api/src/services/notification_service.py` | Service with WebSocket integration |

### NotificationConnectionManager

```python
from src.api.websocket import notification_manager

# Send to single user
await notification_manager.send_to_user(user_id, message)

# Broadcast to multiple users
await notification_manager.broadcast_to_users(user_ids, message)

# Broadcast to all connected users
await notification_manager.broadcast_to_all(message)

# Check if user is connected
is_online = notification_manager.is_user_connected(user_id)

# Get all connected users
connected_users = notification_manager.get_connected_users()
```

### Broadcast Helpers

```python
from src.api.websocket import (
    broadcast_notification,
    broadcast_notification_to_users,
    broadcast_stats_update,
)

# Broadcast new notification to user
await broadcast_notification(
    user_id="uuid",
    notification_data={...},
    event_type="notification:new"
)

# Broadcast to multiple users
await broadcast_notification_to_users(
    user_ids=["uuid1", "uuid2"],
    notification_data={...}
)

# Broadcast stats update
await broadcast_stats_update(
    user_id="uuid",
    stats={"total": 10, "unread": 3, ...}
)
```

### Integration with NotificationService

The notification service automatically broadcasts via WebSocket when:
1. A new notification is created (`create_notification`)
2. Notifications are marked as read (`mark_as_read`)

```python
# In notification_service.py
async def _deliver_notification(self, notification, channels=None):
    # ... deliver via other channels ...

    # Broadcast via WebSocket for real-time updates
    await _broadcast_notification_websocket(notification)
```

## Frontend Implementation

### Files

| File | Description |
|------|-------------|
| `apps/web/hooks/use-notification-websocket.ts` | WebSocket connection hook |
| `apps/web/components/shared/notification-bell.tsx` | Notification bell component |

### useNotificationWebSocket Hook

```typescript
import { useNotificationWebSocket } from "@/hooks/use-notification-websocket";

function MyComponent() {
  const {
    isConnected,
    connectionState,
    connect,
    disconnect,
    lastMessage,
  } = useNotificationWebSocket({
    onNotification: (notification) => {
      // Handle new notification
      toast.info(notification.title);
    },
    onStatsUpdate: (stats) => {
      // Handle stats update
      setUnreadCount(stats.unread);
    },
    onConnect: () => {
      console.log("Connected to WebSocket");
    },
    onDisconnect: () => {
      console.log("Disconnected from WebSocket");
    },
    autoReconnect: true,
    reconnectInterval: 5000,
    maxReconnectAttempts: 10,
  });

  return (
    <div>
      Status: {connectionState}
      {isConnected && <span>🟢 Connected</span>}
    </div>
  );
}
```

### Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `onNotification` | `(data) => void` | - | Called when new notification received |
| `onStatsUpdate` | `(stats) => void` | - | Called when stats update received |
| `onConnect` | `() => void` | - | Called when connected |
| `onDisconnect` | `() => void` | - | Called when disconnected |
| `onError` | `(error) => void` | - | Called on error |
| `autoReconnect` | `boolean` | `true` | Auto reconnect on disconnect |
| `reconnectInterval` | `number` | `5000` | Reconnect delay (ms) |
| `maxReconnectAttempts` | `number` | `10` | Max reconnect attempts |

### Return Values

| Value | Type | Description |
|-------|------|-------------|
| `isConnected` | `boolean` | True if connected |
| `connectionState` | `string` | "connecting", "connected", "disconnected", "error" |
| `connect` | `() => void` | Manually connect |
| `disconnect` | `() => void` | Manually disconnect |
| `lastMessage` | `object` | Last received message |

### NotificationBell Component

The NotificationBell component is included in the Header and provides:
- Bell icon with unread count badge
- Dropdown with recent notifications
- Click to view/mark as read
- Link to full notifications page
- Connection status indicator (green dot = connected)

```typescript
import { NotificationBell } from "@/components/shared";

<Header>
  <NotificationBell />
</Header>
```

## Configuration

### Environment Variables

```env
# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000

# Backend (no additional config needed for WebSocket)
```

### CORS

WebSocket connections use the same CORS settings as the REST API.

## Testing

### Manual Testing

1. Open browser developer tools → Network → WS
2. Look for `/api/v1/ws/notifications` connection
3. Create a notification via API or trigger an event
4. Observe the message in the WebSocket frame

### Test with curl/wscat

```bash
# Install wscat
npm install -g wscat

# Connect (replace TOKEN with valid JWT)
wscat -c "ws://localhost:8000/api/v1/ws/notifications?token=TOKEN"

# Send ping
{"type": "ping"}
```

## Troubleshooting

### Connection Issues

1. **4001 - Missing token**: Ensure token is passed in query string
2. **4002 - Invalid token**: Token may be expired, refresh and reconnect
3. **4003 - Invalid payload**: Token format issue

### No Notifications Received

1. Check WebSocket connection is established (green dot in UI)
2. Verify notification was created in database
3. Check browser console for WebSocket errors
4. Ensure user_id matches notification recipient

### Reconnection Loop

1. Check if token is valid
2. Verify backend is running
3. Check for CORS issues
4. Review maxReconnectAttempts setting

## Performance Considerations

- WebSocket connections are lightweight (~1-2KB memory per connection)
- Ping/pong interval: 30 seconds (adjustable)
- Dead connection cleanup happens automatically
- Multiple tabs share separate connections (user-level grouping)

## Security

- JWT authentication required for connection
- Token passed via query parameter (secure over wss://)
- User can only receive their own notifications
- Connection closed on token expiration
- No message injection possible (server-to-client only for notifications)

## Future Enhancements

- [ ] Presence system (who's online)
- [ ] Typing indicators for collaboration
- [ ] Real-time incident updates
- [ ] Browser push notifications fallback
- [ ] Mobile app push integration
