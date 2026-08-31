import axios from "axios";
import type {
  AxiosError,
  InternalAxiosRequestConfig,
} from "axios";

import {
  refreshAccessToken,
  logout,
} from "./authService";

import { tokenService } from "./tokenService";

const api = axios.create({
  baseURL: "http://127.0.0.1:8000/api",
  headers: {
    "Content-Type": "application/json",
  },
});


/* =========================
   Request Interceptor
========================= */

api.interceptors.request.use(
  (
    config: InternalAxiosRequestConfig
  ) => {

    const accessToken =
      tokenService.getAccessToken();

    if (accessToken) {
      config.headers.Authorization =
        `Bearer ${accessToken}`;
    }

    return config;
  }
);


/* =========================
   Response Interceptor
========================= */

api.interceptors.response.use(

  (response) => {
    return response;
  },

  async (error: AxiosError) => {

    const originalRequest =
      error.config;

    /*
     * فقط خطای 401 را برای Refresh بررسی می‌کنیم.
     */

    if (
      error.response?.status === 401 &&
      originalRequest &&
      !(originalRequest as any)._retry &&
      !originalRequest.url?.includes(
        "/auth/token/"
      )
    ) {

      /*
       * اگر Refresh Token وجود ندارد،
       * دیگر تلاش برای Refresh نکن.
       */

      const refreshToken =
        tokenService.getRefreshToken();

      if (!refreshToken) {
        return Promise.reject(error);
      }


      /*
       * جلوگیری از Loop
       */

      (originalRequest as any)._retry =
        true;


      try {

        const newAccessToken =
          await refreshAccessToken();


        /*
         * درخواست قبلی را
         * با Access Token جدید
         * دوباره ارسال می‌کنیم.
         */

        if (
          originalRequest.headers
        ) {

          originalRequest.headers.Authorization =
            `Bearer ${newAccessToken}`;

        }

        return api(
          originalRequest
        );

      } catch (refreshError) {

        /*
         * Refresh شکست خورد.
         * توکن‌ها را پاک می‌کنیم.
         */

        logout();

        return Promise.reject(
          refreshError
        );
      }
    }

    return Promise.reject(error);
  }
);


export default api;