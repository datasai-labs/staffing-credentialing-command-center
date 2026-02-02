import React from "react";
import {
  DataGrid,
  GridColDef,
  GridPaginationModel,
  GridRowSelectionModel,
  GridSortModel,
  GridToolbar
} from "@mui/x-data-grid";
import { Box } from "@mui/material";

export type ServerTableState = {
  page: number; // 1-based
  pageSize: number;
  sort?: string; // field:asc|desc
};

export function toSortParam(model: GridSortModel): string | undefined {
  if (!model.length) return undefined;
  const s = model[0];
  if (!s.field || !s.sort) return undefined;
  return `${s.field}:${s.sort}`;
}

export function DataTable<T extends { [k: string]: any }>({
  rows,
  columns,
  total,
  loading,
  state,
  onStateChange,
  getRowId,
  onRowClick,
  height = 640,
  csvFileName = "export",
  checkboxSelection,
  rowSelectionModel,
  onRowSelectionModelChange
}: {
  rows: T[];
  columns: GridColDef[];
  total: number;
  loading: boolean;
  state: ServerTableState;
  onStateChange: (s: ServerTableState) => void;
  getRowId: (row: T) => string;
  onRowClick?: (row: T) => void;
  height?: number;
  csvFileName?: string;
  checkboxSelection?: boolean;
  rowSelectionModel?: GridRowSelectionModel;
  onRowSelectionModelChange?: (m: GridRowSelectionModel) => void;
}) {
  const paginationModel: GridPaginationModel = {
    page: state.page - 1,
    pageSize: state.pageSize
  };

  const sortModel: GridSortModel = state.sort
    ? [
        {
          field: state.sort.split(":")[0],
          sort: (state.sort.split(":")[1] as "asc" | "desc") ?? "desc"
        }
      ]
    : [];

  return (
    <Box sx={{ height, width: "100%" }}>
      <DataGrid
        rows={rows}
        columns={columns}
        getRowId={getRowId}
        loading={loading}
        rowCount={total}
        paginationMode="server"
        sortingMode="server"
        checkboxSelection={checkboxSelection}
        rowSelectionModel={rowSelectionModel}
        onRowSelectionModelChange={onRowSelectionModelChange}
        paginationModel={paginationModel}
        onPaginationModelChange={(m) =>
          onStateChange({
            ...state,
            page: m.page + 1,
            pageSize: m.pageSize
          })
        }
        sortModel={sortModel}
        onSortModelChange={(m) => onStateChange({ ...state, sort: toSortParam(m) })}
        onRowClick={(p) => onRowClick?.(p.row as T)}
        disableRowSelectionOnClick
        slots={{ toolbar: GridToolbar }}
        sx={{
          backgroundColor: "background.paper",
          borderColor: "divider",
          borderRadius: 2,
          "& .MuiDataGrid-columnHeaders": {
            backgroundColor: "rgba(11, 95, 174, 0.06)",
            borderBottom: "1px solid rgba(15, 23, 42, 0.12)"
          },
          "& .MuiDataGrid-row:hover": {
            backgroundColor: "rgba(11, 95, 174, 0.04)"
          },
          "& .MuiDataGrid-cell:focus, & .MuiDataGrid-columnHeader:focus": {
            outline: "none"
          }
        }}
        slotProps={{
          toolbar: {
            csvOptions: { fileName: csvFileName },
            printOptions: { disableToolbarButton: true }
          }
        }}
      />
    </Box>
  );
}

