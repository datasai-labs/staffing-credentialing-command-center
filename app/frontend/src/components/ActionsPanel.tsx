import React, { useMemo, useState } from "react";
import {
  Box,
  Button,
  Chip,
  Divider,
  MenuItem,
  Stack,
  TextField,
  Typography
} from "@mui/material";

import { useActions, useCreateAction, useUpdateAction } from "../api/hooks";
import { RiskAction } from "../api/types";
import { ErrorState } from "./States";

function statusColor(s: RiskAction["status"]): "default" | "warning" | "success" {
  if (s === "RESOLVED") return "success";
  if (s === "IN_PROGRESS") return "warning";
  return "default";
}

export function ActionsPanel(props: {
  entityType: "SHIFT" | "PROVIDER";
  entityId: string;
  facilityId?: string;
  defaultActionType?: string;
}) {
  const { entityType, entityId, facilityId } = props;
  const [showNew, setShowNew] = useState(false);
  const [actionType, setActionType] = useState(props.defaultActionType ?? (entityType === "SHIFT" ? "OUTREACH" : "CREDENTIAL_EXPEDITE"));
  const [priority, setPriority] = useState<"LOW" | "MEDIUM" | "HIGH">("MEDIUM");
  const [owner, setOwner] = useState("");
  const [notes, setNotes] = useState("");

  const q = useActions({
    entity_type: entityType,
    entity_id: entityId,
    page: 1,
    page_size: 100,
    sort: "updated_at:desc"
  });

  const create = useCreateAction();
  const update = useUpdateAction();

  const items = q.data?.items ?? [];
  const openCount = useMemo(() => items.filter((a) => a.status !== "RESOLVED").length, [items]);

  return (
    <Stack spacing={1.25}>
      <Stack direction="row" justifyContent="space-between" alignItems="center">
        <Typography variant="h6">Actions</Typography>
        <Stack direction="row" spacing={1} alignItems="center">
          <Chip size="small" label={`${openCount} open`} />
          <Button size="small" variant="contained" onClick={() => setShowNew((v) => !v)}>
            {showNew ? "Cancel" : "Add"}
          </Button>
        </Stack>
      </Stack>

      {showNew ? (
        <Box sx={{ p: 1.25, border: "1px solid", borderColor: "divider", borderRadius: 2, bgcolor: "background.paper" }}>
          <Stack spacing={1}>
            <Stack direction="row" spacing={1}>
              <TextField
                select
                size="small"
                label="Type"
                value={actionType}
                onChange={(e) => setActionType(e.target.value)}
                sx={{ flex: 1 }}
              >
                <MenuItem value="OUTREACH">OUTREACH</MenuItem>
                <MenuItem value="CREDENTIAL_EXPEDITE">CREDENTIAL_EXPEDITE</MenuItem>
                <MenuItem value="PRIVILEGE_REQUEST">PRIVILEGE_REQUEST</MenuItem>
                <MenuItem value="PAYER_ENROLLMENT_FOLLOWUP">PAYER_ENROLLMENT_FOLLOWUP</MenuItem>
              </TextField>
              <TextField
                select
                size="small"
                label="Priority"
                value={priority}
                onChange={(e) => setPriority(e.target.value as any)}
                sx={{ width: 150 }}
              >
                <MenuItem value="LOW">LOW</MenuItem>
                <MenuItem value="MEDIUM">MEDIUM</MenuItem>
                <MenuItem value="HIGH">HIGH</MenuItem>
              </TextField>
            </Stack>

            <TextField
              size="small"
              label="Owner"
              placeholder="e.g. staffing_coordinator"
              value={owner}
              onChange={(e) => setOwner(e.target.value)}
            />
            <TextField
              size="small"
              label="Notes"
              placeholder="What needs to happen next?"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              multiline
              minRows={2}
            />

            <Stack direction="row" spacing={1} justifyContent="flex-end">
              <Button
                size="small"
                variant="contained"
                disabled={create.isPending}
                onClick={async () => {
                  await create.mutateAsync({
                    entity_type: entityType,
                    entity_id: entityId,
                    facility_id: facilityId,
                    action_type: actionType,
                    priority,
                    owner: owner || undefined,
                    notes: notes || undefined
                  });
                  setNotes("");
                  setOwner("");
                  setPriority("MEDIUM");
                  setShowNew(false);
                }}
              >
                Create action
              </Button>
            </Stack>
            {create.isError ? <ErrorState message={(create.error as Error).message} /> : null}
          </Stack>
        </Box>
      ) : null}

      <Divider />

      {q.isLoading ? (
        <Typography variant="body2" color="text.secondary">
          Loading actions…
        </Typography>
      ) : q.isError ? (
        <ErrorState message={(q.error as Error).message} onRetry={() => q.refetch()} />
      ) : items.length ? (
        <Stack spacing={1}>
          {items.map((a) => (
            <Box
              key={a.action_id}
              sx={{ p: 1.25, border: "1px solid", borderColor: "divider", borderRadius: 2, bgcolor: "background.paper" }}
            >
              <Stack spacing={0.75}>
                <Stack direction="row" justifyContent="space-between" alignItems="center" spacing={1}>
                  <Typography variant="body2" sx={{ fontWeight: 600 }}>
                    {a.action_type} • {a.priority}
                  </Typography>
                  <Chip size="small" label={a.status} color={statusColor(a.status)} />
                </Stack>
                <Typography variant="caption" color="text.secondary">
                  Owner: {a.owner ?? "—"} • Updated: {a.updated_at ? new Date(a.updated_at).toLocaleString() : "—"}
                </Typography>
                {a.notes ? (
                  <Typography variant="body2" sx={{ whiteSpace: "pre-wrap" }}>
                    {a.notes}
                  </Typography>
                ) : null}
                <Stack direction="row" spacing={1}>
                  <Button
                    size="small"
                    variant="outlined"
                    disabled={update.isPending || a.status === "IN_PROGRESS" || a.status === "RESOLVED"}
                    onClick={() => update.mutate({ action_id: a.action_id, patch: { status: "IN_PROGRESS" } })}
                  >
                    Start
                  </Button>
                  <Button
                    size="small"
                    variant="contained"
                    disabled={update.isPending || a.status === "RESOLVED"}
                    onClick={() => update.mutate({ action_id: a.action_id, patch: { status: "RESOLVED" } })}
                  >
                    Resolve
                  </Button>
                </Stack>
                {update.isError ? <ErrorState message={(update.error as Error).message} /> : null}
              </Stack>
            </Box>
          ))}
        </Stack>
      ) : (
        <Typography variant="body2" color="text.secondary">
          No actions yet.
        </Typography>
      )}
    </Stack>
  );
}

