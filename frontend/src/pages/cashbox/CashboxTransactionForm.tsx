import { Dialog, DialogActions, DialogContent, DialogTitle, Stack, TextField, Button, Typography } from "@mui/material";

interface Props {
  open: boolean;
  cashboxName?: string;
  type: "deposit" | "withdraw";
  amount: string;
  description: string;
  saving?: boolean;
  onTypeChange: (value: "deposit" | "withdraw") => void;
  onAmountChange: (value: string) => void;
  onDescriptionChange: (value: string) => void;
  onClose: () => void;
  onSubmit: () => void;
}

export default function CashboxTransactionForm({ open, cashboxName, type, amount, description, saving = false, onTypeChange, onAmountChange, onDescriptionChange, onClose, onSubmit }: Props) {
  return (
    <Dialog open={open} onClose={onClose} fullWidth maxWidth="sm">
      <DialogTitle>ثبت عملیات صندوق</DialogTitle>
      <DialogContent>
        <Stack spacing={2} sx={{ mt: 1 }}>
          <Typography sx={{ fontWeight: 700 }}>{cashboxName || "صندوق"}</Typography>
          <TextField select slotProps={{ select: { native: true } }} label="نوع عملیات" value={type} onChange={(e) => onTypeChange(e.target.value as "deposit" | "withdraw")}>
            <option value="deposit">واریز به صندوق</option>
            <option value="withdraw">برداشت از صندوق</option>
          </TextField>
          <TextField label="مبلغ" type="number" value={amount} onChange={(e) => onAmountChange(e.target.value)} slotProps={{ htmlInput: { min: 1 } }} required />
          <TextField label="شرح" value={description} onChange={(e) => onDescriptionChange(e.target.value)} multiline minRows={2} />
        </Stack>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>انصراف</Button>
        <Button variant="contained" onClick={onSubmit} disabled={saving || Number(amount) <= 0}>ثبت عملیات</Button>
      </DialogActions>
    </Dialog>
  );
}
