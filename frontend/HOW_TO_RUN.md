# How to Run the Smart Parking Frontend

## Prerequisites

Make sure you have the following installed:
- **Node.js** (version 18 or higher)
- **npm** (comes with Node.js)

## Step-by-Step Instructions

### 1. Navigate to the Frontend Directory
```bash
cd /Users/manojdeka/Documents/Interviews/FuelCycle/frontend
```

### 2. Install Dependencies (if not already done)
```bash
npm install
```

### 3. Start the Development Server
```bash
npm start
```
**OR**
```bash
ng serve
```

### 4. Access the Application
Once the server starts, open your browser and go to:
```
http://localhost:4200
```

## Available Scripts

- **`npm start`** - Start the development server
- **`npm run build`** - Build the app for production
- **`npm run watch`** - Build in watch mode for development
- **`npm test`** - Run unit tests
- **`npm run lint`** - Lint the code

## Backend Connection

The frontend is configured to connect to the backend API at:
```
http://localhost:8000/api/v1
```

Make sure your backend is running on port 8000 before using the frontend.

## Default Login

If you need test credentials, you can register a new account or use any existing user credentials from your backend.

## Features Available

✅ **Authentication**
- User registration and login
- Protected routes with auth guard

✅ **Dashboard**
- User overview with statistics
- Quick actions for booking and searching

✅ **Parking Search**
- Search form with vehicle type, time, and location
- Geolocation support for nearby parking lots
- Real-time availability display

✅ **Responsive Design**
- Mobile-first Bootstrap 5 UI
- Works on all device sizes

## Browser Compatibility

The app works on:
- Chrome (recommended)
- Firefox
- Safari
- Edge

## Development Notes

- The app uses Angular 18+ with standalone components
- Bootstrap 5 for styling
- Reactive forms for better user experience
- Lazy loading for optimal performance

## Troubleshooting

**If you get port conflicts:**
```bash
ng serve --port 4201
```

**If dependencies are missing:**
```bash
rm -rf node_modules package-lock.json
npm install
```

**For CORS issues:**
Make sure your backend allows requests from `http://localhost:4200`
