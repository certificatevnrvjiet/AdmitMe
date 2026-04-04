# AdmitMe Frontend

The user interface for the AdmitMe Student Verification System, built with **React**, **Vite**, and **TailwindCSS**.

## 🚀 Getting Started

1.  **Install dependencies**:
    ```bash
    npm install
    ```

2.  **Configure Environment**:
    Create a `.env` file in the `frontend/` directory:
    ```env
    VITE_API_URL=http://localhost:8000
    ```

3.  **Run Development Server**:
    ```bash
    npm run dev
    ```

## 📂 Internal Structure

- `src/components`: Reusable UI building blocks (Layout, Sidebar, Modals).
- `src/context`: React Context providers for global state (Authentication, Notifications).
- `src/pages`: High-level page components (Dashboard, Login, Student Details).
- `src/services`: API abstraction layer for communicating with the FastAPI backend.

## 🛠 Tech Stack
- **Framework**: React 18+ (Vite)
- **Styling**: TailwindCSS
- **Icons**: Lucide React / React Icons
- **HTTP Client**: Axios
- **Routing**: React Router DOM
