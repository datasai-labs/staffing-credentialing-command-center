import React from "react";
import { createBrowserRouter, Navigate } from "react-router-dom";

import { App } from "./App";
import { RouteError } from "./RouteError";
import { Overview } from "../pages/Overview";
import { StaffingGaps } from "../pages/StaffingGaps";
import { ProviderDirectory } from "../pages/ProviderDirectory";
import { ProviderDetail } from "../pages/ProviderDetail";
import { CredentialRisk } from "../pages/CredentialRisk";

export const routes = createBrowserRouter([
  {
    path: "/",
    element: <App />,
    errorElement: <RouteError />,
    children: [
      { index: true, element: <Overview /> },
      { path: "staffing", element: <StaffingGaps /> },
      { path: "providers", element: <ProviderDirectory /> },
      { path: "providers/:id", element: <ProviderDetail /> },
      { path: "credentials", element: <CredentialRisk /> },
      { path: "*", element: <Navigate to="/" replace /> }
    ]
  }
]);

