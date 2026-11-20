import { useEffect } from "react";
import { useTranslation } from "react-i18next";

import { Footer } from "./components/Footer";

const SUPPORTED_LANGUAGES = [
  { code: "pt-BR", labelKey: "languageSwitcher.ptBR" },
  { code: "en", labelKey: "languageSwitcher.en" },
] as const;

type SupportedLanguage = (typeof SUPPORTED_LANGUAGES)[number]["code"];

export function App() {
  const { t, i18n } = useTranslation();
  const currentLanguage: SupportedLanguage =
    i18n.language === "en" ? "en" : "pt-BR";

  useEffect(() => {
    document.documentElement.lang = currentLanguage;
  }, [currentLanguage]);

  const handleLanguageChange = (language: SupportedLanguage) => {
    void i18n.changeLanguage(language);
  };

  return (
    <div className="flex min-h-screen flex-col bg-slate-950 text-slate-100">
      <header className="border-b border-slate-800 px-6 py-4">
        <div className="mx-auto flex max-w-4xl items-center justify-between gap-4">
          <span className="text-sm font-semibold tracking-wider text-amber-400 uppercase">
            {t("brand")}
          </span>
          <div
            role="group"
            aria-label={t("languageSwitcher.label")}
            className="flex items-center gap-2"
          >
            {SUPPORTED_LANGUAGES.map(({ code, labelKey }) => {
              const isActive = currentLanguage === code;
              return (
                <button
                  key={code}
                  type="button"
                  aria-pressed={isActive}
                  onClick={() => handleLanguageChange(code)}
                  className={
                    isActive
                      ? "rounded-md bg-amber-400 px-3 py-1.5 text-xs font-semibold text-slate-950 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-amber-300"
                      : "rounded-md border border-slate-700 bg-slate-900 px-3 py-1.5 text-xs font-medium text-slate-200 hover:bg-slate-800 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-amber-300"
                  }
                >
                  {t(labelKey)}
                </button>
              );
            })}
          </div>
        </div>
      </header>

      <main className="mx-auto flex w-full max-w-4xl flex-1 flex-col justify-center px-6 py-16">
        <div className="space-y-6">
          <h1 className="text-4xl font-bold tracking-tight text-slate-50 sm:text-5xl">
            {t("brand")}
          </h1>
          <p className="max-w-2xl text-lg text-slate-300">{t("tagline")}</p>
          <p className="inline-block rounded-lg border border-slate-800 bg-slate-900/70 px-4 py-3 text-sm text-slate-300">
            {t("statusNotice")}
          </p>
        </div>
      </main>

      <Footer />
    </div>
  );
}

export default App;
