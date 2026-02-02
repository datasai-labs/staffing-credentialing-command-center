import React from "react";
import { isRouteErrorResponse, useRouteError } from "react-router-dom";
import { Alert, Box, Button, Stack, Typography } from "@mui/material";

export function RouteError() {
  const err = useRouteError();

  let title = "Something went wrong";
  let message = "An unexpected error occurred while rendering this page.";

  if (isRouteErrorResponse(err)) {
    title = `Error ${err.status}`;
    message = typeof err.data === "string" ? err.data : err.statusText;
  } else if (err instanceof Error) {
    message = err.message;
  }

  return (
    <Box sx={{ p: 3 }}>
      <Stack spacing={2}>
        <Typography variant="h5">{title}</Typography>
        <Alert severity="error">
          <Typography variant="body2">{message}</Typography>
        </Alert>
        <Box>
          <Button variant="contained" onClick={() => window.location.reload()}>
            Reload
          </Button>
        </Box>
      </Stack>
    </Box>
  );
}

