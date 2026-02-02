import React from "react";
import { Alert, Box, Button, Skeleton, Stack, Typography } from "@mui/material";

export function LoadingSkeleton({ rows = 8 }: { rows?: number }) {
  return (
    <Stack spacing={1}>
      {Array.from({ length: rows }).map((_, i) => (
        <Skeleton key={i} variant="rectangular" height={36} />
      ))}
    </Stack>
  );
}

export function EmptyState({
  title = "No results",
  description
}: {
  title?: string;
  description?: string;
}) {
  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h6">{title}</Typography>
      {description ? (
        <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
          {description}
        </Typography>
      ) : null}
    </Box>
  );
}

export function ErrorState({
  title = "Something went wrong",
  message,
  onRetry
}: {
  title?: string;
  message?: string;
  onRetry?: () => void;
}) {
  return (
    <Alert
      severity="error"
      action={
        onRetry ? (
          <Button color="inherit" size="small" onClick={onRetry}>
            Retry
          </Button>
        ) : undefined
      }
    >
      <Typography variant="subtitle2">{title}</Typography>
      {message ? <Typography variant="body2">{message}</Typography> : null}
    </Alert>
  );
}

