import { Dialog, DialogActions, DialogContent, DialogTitle, Stack, TextField, Button } from "@mui/material";

interface Props {
  open: boolean;
  editing: boolean;
  name: string;
  description: string;
  saving?: boolean;
  onNameChange: (value: string) => void;
  onDescriptionChange: (value: string) => void;
  onClose: () => void;
  onSubmit: () => void;
}

export default function CashboxForm({ open, editing, name, description, saving = false, onNameChange, onDescriptionChange, onClose, onSubmit }: Props) {
  return (
    <Dialog open={open} onClose={onClose} fullWidth maxWidth="sm">
      <DialogTitle>{editing ? "ویرایش صندوق" : "ثبت صندوق جدید"}</DialogTitle>
      <DialogContent>
        <Stack spacing={2} sx={{ mt: 1 }}>
          <TextField label="نام صندوق" value={name} onChange={(e) => onNameChange(e.target.value)} autoFocus required />
          <TextField label="توضیحات" multiline minRows={3} value={description} onChange={(e) => onDescriptionChange(e.target.value)} />
        </Stack>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>انصراف</Button>
        <Button variant="contained" onClick={onSubmit} disabled={saving || !name.trim()}>
          {saving ? "در حال ذخیره..." : "ذخیره صندوق"}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
