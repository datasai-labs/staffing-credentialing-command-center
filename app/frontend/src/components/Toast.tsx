import React, { createContext, useCallback, useContext, useMemo, useState } from "react";
import { Alert, Snackbar } from "@mui/material";

type ToastSeverity = "success" | "info" | "warning" | "error";

type ToastState = {
  open: boolean;
  message: string;
  severity: ToastSeverity;
};

type ToastApi = {
  show: (message: string, severity?: ToastSeverity) => void;
};

const Ctx = createContext<ToastApi | null>(null);

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [state, setState] = useState<ToastState>({
    open: false,
    message: "",
    severity: "info"
  });

  const show = useCallback((message: string, severity: ToastSeverity = "info") => {
    setState({ open: true, message, severity });
  }, []);

  const api = useMemo(() => ({ show }), [show]);

  return (
    <Ctx.Provider value={api}>
      {children}
      <Snackbar
        open={state.open}
        autoHideDuration={4000}
        onClose={() => setState((s) => ({ ...s, open: false }))}
        anchorOrigin={{ vertical: "bottom", horizontal: "right" }}
      >
        <Alert
          onClose={() => setState((s) => ({ ...s, open: false }))}
          severity={state.severity}
          variant="filled"
          sx={{ width: "100%" }}
        >
          {state.message}
        </Alert>
      </Snackbar>
    </Ctx.Provider>
  );
}

export function useToast() {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error("useToast must be used within ToastProvider");
  return ctx;
}

