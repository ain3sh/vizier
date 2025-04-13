# vizier

## Introduction

Vizier is a research co-pilot application that helps users find, organize, and synthesize information. The frontend is built with React, TypeScript, and Vite, providing an intuitive and responsive user interface.

## Prerequisites

Before installing the Vizier frontend, ensure you have the following installed:

- [Node.js](https://nodejs.org/) (v18 or later recommended)
- [npm](https://www.npmjs.com/) (v9 or later) or [yarn](https://yarnpkg.com/)
- A code editor like [Visual Studio Code](https://code.visualstudio.com/)

## Installation

Follow these steps to set up the Vizier frontend locally:

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/vizier.git
   cd vizier
   ```

2. Navigate to the frontend directory:
   ```bash
   cd vizier-frontend
   ```

3. Install dependencies:
   ```bash
   npm install
   # or
   yarn
   ```

## Configuration

The application connects to a backend API. By default, it points to `http://localhost:8000`. If you need to change this:

1. Open `src/app/pages/query/query-with-api.tsx`
2. Locate the `API_BASE_URL` constant and update it:
   ```typescript
   const API_BASE_URL = 'http://your-backend-url';
   ```

## Running the Application

### Development Mode

To start the application in development mode with hot-reloading:

```bash
npm run dev
# or
yarn dev
```

This will start the development server at `http://localhost:5173` (or the next available port).

### Production Build

To create a production build:

```bash
npm run build
# or
yarn build
```

To preview the production build locally:

```bash
npm run preview
# or
yarn preview
```

## Project Structure

```
vizier-frontend/
├── public/                # Static files
├── src/
│   ├── app/
│   │   ├── pages/         # Application pages
│   │   │   ├── discover/  # Discover page
│   │   │   ├── graph/     # Graph visualization
│   │   │   ├── library/   # Library page
│   │   │   ├── login/     # Login and authentication
│   │   │   ├── onboarding/# User onboarding
│   │   │   ├── query/     # Query interface
│   │   │   ├── settings/  # Settings page
│   │   │   └── spaces/    # Spaces page
│   │   ├── App.tsx        # Main application component
│   │   ├── App.css        # Main application styles
│   │   ├── index.css      # Global styles
│   │   └── main.tsx       # Application entry point
│   ├── components/        # Reusable components
│   │   ├── navigation/    # Navigation components
│   │   └── querybar/      # Query bar components
│   └── vite-env.d.ts      # Vite environment typings
├── index.html             # HTML entry point
├── tsconfig.json          # TypeScript configuration
├── tsconfig.app.json      # App-specific TypeScript config
├── tsconfig.node.json     # Node-specific TypeScript config
├── vite.config.ts         # Vite configuration
├── package.json           # Project dependencies and scripts
└── README.md              # Project documentation
```

## Key Features

### Authentication

The application uses Google OAuth for authentication. When users log in, a JWT token is stored in localStorage for subsequent API requests.

### Navigation
(Currently unimplemented)
The sidebar navigation allows users to move between different sections of the application:
- Home
- Discover
- Spaces
- Library
- Settings

### Query Interface

The query interface allows users to:
1. Enter natural language queries
2. Refine queries with AI assistance
3. Review and edit sources
4. Generate and edit drafts

### Graph Visualization

The graph page provides a visual representation of agent workflows and query processing.

## Troubleshooting

### Backend Connection Issues

If you encounter issues connecting to the backend:

1. Ensure the backend server is running
2. Check that the `API_BASE_URL` is correctly set
3. Verify network connectivity between frontend and backend

### Authentication Problems

If login doesn't work:

1. Check the browser console for errors
2. Ensure the Google OAuth client ID is correctly configured in `login.tsx`
3. Verify that the backend authentication callback URL is correct

### Build Errors

If you encounter build errors:

1. Update dependencies: `npm update` or `yarn upgrade`
2. Clean the build cache: remove the `dist` and `node_modules/.tmp` folders
3. Reinstall dependencies: `npm install` or `yarn`

## Contributing

To contribute to the Vizier frontend:

1. Create a feature branch: `git checkout -b feature/your-feature-name`
2. Make your changes
3. Run linting: `npm run lint` or `yarn lint`
4. Test your changes thoroughly
5. Submit a pull request

## Additional Resources

- [React Documentation](https://react.dev/)
- [TypeScript Documentation](https://www.typescriptlang.org/docs/)
- [Vite Documentation](https://vitejs.dev/guide/)
- [React Router Documentation](https://reactrouter.com/en/main)
