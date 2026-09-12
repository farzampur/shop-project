let accessToken: string | null = null;

function decodePayload(token: string): Record<string, unknown> | null {
  try {
    const payload = token.split(".")[1];

    if (!payload) {
      return null;
    }

    const normalized = payload.replace(/-/g, "+").replace(/_/g, "/");

    const json = decodeURIComponent(
      atob(
        normalized.padEnd(
          normalized.length + ((4 - (normalized.length % 4)) % 4),
          "="
        )
      )
        .split("")
        .map(
          (char) =>
            `%${(`00${char.charCodeAt(0).toString(16)}`).slice(-2)}`
        )
        .join("")
    );

    return JSON.parse(json);
  } catch {
    return null;
  }
}

export const tokenService = {
  saveAccessToken(token: string) {
    accessToken = token;
  },

  getAccessToken(): string | null {
    return accessToken;
  },

  isAccessTokenExpired(leewaySeconds = 15): boolean {
    const token = accessToken;

    if (!token) {
      return true;
    }

    const payload = decodePayload(token);
    const exp = payload?.exp;

    if (typeof exp !== "number") {
      return true;
    }

    return exp <= Math.floor(Date.now() / 1000) + leewaySeconds;
  },

  clearTokens() {
    accessToken = null;
  },
};