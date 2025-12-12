# Toast Notification System

The toast notification system provides beautiful, animated notifications for user feedback.

## Usage

### Import
```javascript
import { showToast } from './components/Toast'
```

### Examples

#### Success Toast
```javascript
showToast('Payment processed successfully!', 'success')
showToast('Account upgraded to Premium!', 'success', 4000) // Custom duration
```

#### Error Toast
```javascript
showToast('Failed to connect to server', 'error')
showToast('Invalid credentials', 'error')
```

#### Warning Toast
```javascript
showToast('Your session will expire in 5 minutes', 'warning')
showToast('Please verify your email', 'warning')
```

#### Info Toast
```javascript
showToast('New signals available!', 'info')
showToast('Market update received', 'info')
```

## Parameters

- `message` (string): The message to display
- `type` (string): 'success' | 'error' | 'warning' | 'info' (default: 'info')
- `duration` (number): Duration in milliseconds (default: 3000)

## Features

- ✓ Auto-dismiss after duration
- ✓ Manual close button
- ✓ Progress bar animation
- ✓ Smooth slide-down entrance
- ✓ Color-coded by type with glow effects
- ✓ Glassmorphism backdrop blur
- ✓ Stacks multiple toasts vertically
- ✓ Mobile responsive

## Example Integration

### In Dashboard.jsx
```javascript
import { showToast } from '../components/Toast'

// On successful data load
useEffect(() => {
  if (coins.length > 0) {
    showToast(`${coins.length} coins loaded`, 'success')
  }
}, [coins])

// On error
catch (error) {
  showToast('Failed to load data', 'error')
}
```

### In Login.jsx
```javascript
import { showToast } from './components/Toast'

const handleLogin = async () => {
  try {
    const response = await login(email, password)
    showToast('Welcome back!', 'success')
  } catch (error) {
    showToast('Login failed', 'error')
  }
}
```

### In Premium.jsx
```javascript
import { showToast } from '../components/Toast'

const handlePayment = () => {
  showToast('Payment notification sent to admin', 'info', 5000)
}
```

## Styling

Toast notifications use Tailwind CSS with custom animations:
- Smooth slide-down entrance (`animate-slide-down`)
- Progress bar countdown (`animate-progress`)
- Glassmorphism backdrop blur
- Color-coded shadows (green, red, yellow, blue)
- Responsive width (min 300px, max 28rem)
