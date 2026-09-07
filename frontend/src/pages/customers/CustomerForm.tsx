import { Dialog, DialogActions, DialogContent, DialogTitle, Stack, TextField, Button } from "@mui/material";

export type CustomerFormState = { first_name: string; last_name: string; mobile: string; address: string };

interface Props {
  open: boolean;
  editing: boolean;
  form: CustomerFormState;
  saving?: boolean;
  onChange: (form: CustomerFormState) => void;
  onClose: () => void;
  onSubmit: () => void;
}

export default function CustomerForm({ open, editing, form, saving = false, onChange, onClose, onSubmit }: Props) {
  return (
    <Dialog open={open} onClose={onClose} fullWidth maxWidth="sm">
      <DialogTitle>{editing ? "ویرایش مشتری" : "ثبت مشتری جدید"}</DialogTitle>
      <DialogContent>
        <Stack spacing={2} sx={{ mt: 1 }}>
          <TextField label="نام" value={form.first_name} onChange={(e) => onChange({ ...form, first_name: e.target.value })} autoFocus required />
          <TextField label="نام خانوادگی" value={form.last_name} onChange={(e) => onChange({ ...form, last_name: e.target.value })} />
          <TextField label="موبایل" value={form.mobile} onChange={(e) => onChange({ ...form, mobile: e.target.value })} required />
          <TextField label="آدرس" multiline minRows={3} value={form.address} onChange={(e) => onChange({ ...form, address: e.target.value })} />
        </Stack>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>انصراف</Button>
        <Button variant="contained" onClick={onSubmit} disabled={saving || !form.first_name.trim() || !form.mobile.trim()}>
          {saving ? "در حال ذخیره..." : "ذخیره مشتری"}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
