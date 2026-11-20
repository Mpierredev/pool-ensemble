import { useTranslation } from "react-i18next";

export function Footer() {
  const { t } = useTranslation();

  return (
    <footer className="border-t border-slate-800 bg-slate-950/80 px-6 py-6">
      <div className="mx-auto max-w-4xl space-y-2 text-xs leading-relaxed text-slate-300">
        <p>{t("legal.disclaimer")}</p>
        <p className="text-slate-400">{t("legal.jibberJabber")}</p>
      </div>
    </footer>
  );
}
