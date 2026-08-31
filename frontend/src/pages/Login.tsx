import { useState } from "react";
import {
  Alert,
  Box,
  Button,
  CircularProgress,
  Paper,
  TextField,
  Typography,
} from "@mui/material";
import { login, saveTokens } from "../services/authService";
import {
  useNavigate,
} from "react-router-dom";

function Login() {
  const navigate = useNavigate();	
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleLogin = async (event: React.FormEvent) => {
    event.preventDefault();

    setError("");
    setLoading(true);

    try {
      const tokens = await login(username, password);

	  console.log("TOKENS FROM LOGIN:", tokens);

  	  saveTokens(tokens);
	  window.dispatchEvent(
	    new Event("auth-change")
	  );
	  console.log(
	    "ACCESS AFTER SAVE:",
	    localStorage.getItem("access_token")
	  );

	  console.log(
	    "REFRESH AFTER SAVE:",
	    localStorage.getItem("refresh_token")
	  );

      console.log("Login successful");
	  navigate("/dashboard", {
		  replace: true,
      });
    } catch (error: any) {
	  console.error("LOGIN ERROR:", error);
	  console.error("STATUS:", error.response?.status);
	  console.error("DATA:", error.response?.data);

	  setError(
		error.response?.data
		  ? JSON.stringify(error.response.data)
		  : "خطا در ارتباط با سرور"
	  );
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box
      sx={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        direction: "rtl",
        p: 2,
      }}
    >
      <Paper
        elevation={4}
        sx={{
          width: "100%",
          maxWidth: 420,
          p: 4,
        }}
      >
        <Typography
          variant="h4"
          sx={{
            textAlign: "right",
            mb: 1,
          }}
        >
          فروشگاه من
        </Typography>

        <Typography
          variant="body1"
          sx={{
            textAlign: "right",
            mb: 3,
          }}
        >
          ورود به حساب کاربری
        </Typography>

        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        <Box component="form" onSubmit={handleLogin}>
          <TextField
            fullWidth
            label="نام کاربری"
            value={username}
            onChange={(event) => setUsername(event.target.value)}
            margin="normal"
            autoComplete="username"
          />

          <TextField
            fullWidth
            label="رمز عبور"
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            margin="normal"
            autoComplete="current-password"
          />

          <Button
            type="submit"
            fullWidth
            variant="contained"
            disabled={loading}
            sx={{ mt: 3, py: 1.2 }}
          >
            {loading ? <CircularProgress size={24} /> : "ورود"}
          </Button>
        </Box>
      </Paper>
    </Box>
  );
}

export default Login;