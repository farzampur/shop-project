const fieldLabels: Record<string, string> = {
  username: "نام کاربری",
  password: "رمز عبور",
  refresh: "نشست ورود",
  access: "نشست ورود",
  email: "ایمیل",
  mobile: "شماره همراه",
  first_name: "نام",
  last_name: "نام خانوادگی",
  name: "نام",
  barcode: "بارکد",
  category: "دسته‌بندی",
  product: "کالا",
  products: "کالاها",
  supplier: "تأمین‌کننده",
  customer: "مشتری",
  store: "فروشگاه",
  cashbox: "صندوق",
  cashbox_id: "صندوق",
  amount: "مبلغ",
  quantity: "تعداد",
  unit_price: "قیمت واحد",
  sale_price: "قیمت فروش",
  payments: "پرداخت‌ها",
  items: "اقلام",
  start_date: "تاریخ شروع",
  end_date: "تاریخ پایان",
  effective_from: "تاریخ شروع اعتبار",
  effective_to: "تاریخ پایان اعتبار",
  price_type: "نوع قیمت",
  transfer: "انتقال",
  destination_store: "فروشگاه مقصد",
  source_store: "فروشگاه مبدأ",
  counted_balance: "موجودی شمارش‌شده",
  description: "توضیحات",
};

const exactMessages: Record<string, string> = {
  "No active account found with the given credentials": "نام کاربری یا رمز عبور اشتباه است.",
  "Refresh token cookie is required.": "نشست ورود شما پیدا نشد یا منقضی شده است. لطفاً دوباره وارد شوید.",
  "Given token not valid for any token type": "نشست ورود معتبر نیست. لطفاً دوباره وارد شوید.",
  "Token is invalid or expired": "نشست ورود منقضی یا نامعتبر است. لطفاً دوباره وارد شوید.",
  "Token is expired": "نشست ورود منقضی شده است. لطفاً دوباره وارد شوید.",
  "Token is blacklisted": "این نشست دیگر معتبر نیست. لطفاً دوباره وارد شوید.",
  "Authentication credentials were not provided.": "برای انجام این عملیات باید وارد حساب کاربری شوید.",
  "You do not have permission to perform this action.": "شما اجازه انجام این عملیات را ندارید.",
  "Not found.": "اطلاعات موردنظر پیدا نشد.",
  "Method \"GET\" not allowed.": "این عملیات برای این بخش مجاز نیست.",
  "Method \"POST\" not allowed.": "ثبت این عملیات در این بخش مجاز نیست.",
  "Method \"PUT\" not allowed.": "ویرایش این عملیات در این بخش مجاز نیست.",
  "Method \"PATCH\" not allowed.": "ویرایش این عملیات در این بخش مجاز نیست.",
  "Method \"DELETE\" not allowed.": "حذف این عملیات در این بخش مجاز نیست.",
  "Request was throttled.": "تعداد درخواست‌ها بیش از حد مجاز است. کمی بعد دوباره تلاش کنید.",
  "Network Error": "ارتباط با سرور برقرار نشد. اتصال شبکه را بررسی کنید.",
};

function normalizeText(value: string): string {
  const trimmed = value.trim();
  if (!trimmed) return "";
  return exactMessages[trimmed] ?? trimmed;
}

function labelFor(key: string): string {
  const normalized = key.replace(/\[\d+\]/g, "");
  return fieldLabels[normalized] ?? normalized.replace(/_/g, " ");
}

function translateCommonValidation(text: string): string {
  const normalized = text.trim();
  const direct = exactMessages[normalized];
  if (direct) return direct;

  if (/No active account found with the given credentials/i.test(normalized)) {
    return "نام کاربری یا رمز عبور اشتباه است.";
  }
  if (/Origin checking failed|CSRF Failed|CSRF verification failed/i.test(normalized)) {
    return "درخواست از نظر امنیتی تأیید نشد. صفحه را تازه‌سازی کنید و دوباره تلاش کنید.";
  }
  if (/Failed to fetch|Network request failed|Connection (?:aborted|reset|refused)/i.test(normalized)) {
    return "ارتباط با سرور برقرار نشد. اتصال شبکه را بررسی کنید.";
  }
  if (/^Request failed with status code \d+$/i.test(normalized)) {
    return "درخواست با خطا مواجه شد.";
  }

  if (/^This field is required\.?$/i.test(normalized)) return "این فیلد الزامی است.";
  if (/^This field may not be blank\.?$/i.test(normalized)) return "این فیلد نمی‌تواند خالی باشد.";
  if (/^This field may not be null\.?$/i.test(normalized)) return "این فیلد نمی‌تواند خالی باشد.";
  if (/^This field must be unique\.?$/i.test(normalized)) return "این مقدار قبلاً ثبت شده است و باید مقدار دیگری وارد کنید.";
  if (/^Enter a valid email address\.?$/i.test(normalized)) return "یک ایمیل معتبر وارد کنید.";
  if (/^A valid integer is required\.?$/i.test(normalized)) return "یک عدد صحیح معتبر وارد کنید.";
  if (/^A valid number is required\.?$/i.test(normalized)) return "یک عدد معتبر وارد کنید.";
  if (/^Enter a valid URL\.?$/i.test(normalized)) return "یک نشانی معتبر وارد کنید.";
  if (/^Ensure this value has at least (\d+) characters?\.?$/i.test(normalized)) {
    const [, n] = normalized.match(/^Ensure this value has at least (\d+) characters?\.?$/i) ?? [];
    return `این مقدار باید حداقل ${n} کاراکتر داشته باشد.`;
  }
  if (/^Ensure this value has at most (\d+) characters?\.?$/i.test(normalized)) {
    const [, n] = normalized.match(/^Ensure this value has at most (\d+) characters?\.?$/i) ?? [];
    return `این مقدار باید حداکثر ${n} کاراکتر داشته باشد.`;
  }
  if (/^Ensure this value is greater than or equal to (.+)\.?$/i.test(normalized)) {
    const [, n] = normalized.match(/^Ensure this value is greater than or equal to (.+)\.?$/i) ?? [];
    return `مقدار باید بزرگ‌تر یا مساوی ${n} باشد.`;
  }
  if (/^Ensure this value is less than or equal to (.+)\.?$/i.test(normalized)) {
    const [, n] = normalized.match(/^Ensure this value is less than or equal to (.+)\.?$/i) ?? [];
    return `مقدار باید کوچک‌تر یا مساوی ${n} باشد.`;
  }
  if (/^Invalid pk .*? - object does not exist\.?$/i.test(normalized)) return "اطلاعات انتخاب‌شده پیدا نشد.";
  if (/^Incorrect type\./i.test(normalized)) return "نوع اطلاعات واردشده صحیح نیست.";
  if (/^Date has wrong format\./i.test(normalized)) return "فرمت تاریخ واردشده صحیح نیست.";
  if (/^Datetime has wrong format\./i.test(normalized)) return "فرمت تاریخ و زمان واردشده صحیح نیست.";
  if (/^Invalid data\.?$/i.test(normalized)) return "اطلاعات واردشده معتبر نیست.";

  return normalizeText(normalized);
}

function flatten(value: unknown): string[] {
  if (value == null) return [];
  if (typeof value === "string") return [translateCommonValidation(value)];
  if (typeof value === "number" || typeof value === "boolean") return [String(value)];
  if (Array.isArray(value)) return value.flatMap(flatten);
  if (typeof value === "object") {
    return Object.entries(value as Record<string, unknown>).flatMap(([key, child]) => {
      const messages = flatten(child);
      if (!messages.length) return [];
      return [messages.length === 1 && key !== "detail" && key !== "message"
        ? `${labelFor(key)}: ${messages[0]}`
        : messages.join(" ")];
    });
  }
  return [];
}

export function getApiErrorMessage(error: unknown, fallback = "عملیات انجام نشد."): string {
  const candidate = error as {
    response?: { data?: unknown; status?: number };
    message?: unknown;
    code?: unknown;
  } | null;

  const status = candidate?.response?.status;
  const data = candidate?.response?.data;

  if (typeof data === "string") {
    const message = translateCommonValidation(data);
    if (message) return message;
  }

  if (data && typeof data === "object") {
    const record = data as Record<string, unknown>;

    for (const key of ["detail", "message", "error", "non_field_errors"]) {
      const value = record[key];
      const messages = flatten(value);
      if (messages.length) return messages.join(" ");
    }

    const fieldMessages = flatten(data);
    if (fieldMessages.length) return fieldMessages.join(" ");
  }

  if (typeof candidate?.message === "string" && candidate.message.trim()) {
    const message = translateCommonValidation(candidate.message);
    if (message && message !== "Request failed with status code 401" && message !== "Request failed with status code 400") {
      return message;
    }
  }

  if (candidate?.code === "ERR_NETWORK") return "ارتباط با سرور برقرار نشد. اتصال شبکه را بررسی کنید.";
  if (candidate?.code === "ECONNABORTED") return "پاسخ سرور بیش از حد طول کشید. دوباره تلاش کنید.";

  switch (status) {
    case 400: return "اطلاعات ارسال‌شده معتبر نیست. موارد واردشده را بررسی کنید.";
    case 401: return "نشست شما معتبر نیست یا منقضی شده است. لطفاً دوباره وارد شوید.";
    case 403: return "شما اجازه انجام این عملیات را ندارید.";
    case 404: return "اطلاعات موردنظر پیدا نشد.";
    case 405: return "این عملیات برای این بخش مجاز نیست.";
    case 409: return "این عملیات با اطلاعات موجود ناسازگار است یا این مورد قبلاً ثبت شده است.";
    case 413: return "حجم اطلاعات ارسالی بیش از حد مجاز است.";
    case 415: return "نوع اطلاعات ارسالی پشتیبانی نمی‌شود.";
    case 429: return "تعداد درخواست‌ها بیش از حد مجاز است. کمی بعد دوباره تلاش کنید.";
    case 500: return "خطای داخلی سرور رخ داده است. دوباره تلاش کنید.";
    case 502:
    case 503:
    case 504: return "سرور موقتاً در دسترس نیست. کمی بعد دوباره تلاش کنید.";
    default: return fallback;
  }
}
