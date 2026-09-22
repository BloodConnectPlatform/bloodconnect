const DEFAULT_WHATSAPP_NUMBER = '918807864003';

let cachedWhatsAppNumber: string | null = null;

export const setCachedWhatsAppNumber = (num: string) => {
  if (num && num.trim()) {
    cachedWhatsAppNumber = num.replace(/\D/g, '');
  }
};

export const getWhatsAppNumber = (): string => {
  if (cachedWhatsAppNumber) {
    return cachedWhatsAppNumber;
  }
  const envNum = process.env.NEXT_PUBLIC_WHATSAPP_NUMBER || process.env.WHATSAPP_NUMBER;
  if (envNum && envNum.trim()) {
    return envNum.replace(/\D/g, '');
  }
  return DEFAULT_WHATSAPP_NUMBER;
};

export const getWhatsAppLoginUrl = (commandText: string = 'LOGIN'): string => {
  const number = getWhatsAppNumber();
  return `https://wa.me/${number}?text=${encodeURIComponent(commandText)}`;
};

export const redirectToWhatsAppLogin = (commandText: string = 'LOGIN'): void => {
  if (typeof window === 'undefined') return;
  const url = getWhatsAppLoginUrl(commandText);
  window.location.href = url;
};

// Asynchronously sync config from backend if available
export const fetchAndSyncWhatsAppConfig = async (): Promise<string> => {
  try {
    const res = await fetch('/api/v1/auth/whatsapp/config');
    if (res.ok) {
      const data = await res.json();
      if (data.whatsapp_phone_number) {
        setCachedWhatsAppNumber(data.whatsapp_phone_number);
        return data.whatsapp_phone_number;
      }
    }
  } catch {
    // Fallback to default
  }
  return getWhatsAppNumber();
};
