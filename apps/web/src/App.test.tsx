import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it } from "vitest";

import App from "./App";
import i18n from "./i18n";

describe("App", () => {
  beforeEach(async () => {
    await i18n.changeLanguage("pt-BR");
  });

  afterEach(() => {
    cleanup();
  });

  it("renders the heading and Riot legal disclaimer in pt-BR by default", () => {
    render(<App />);

    expect(
      screen.getByRole("heading", { name: "Pool Ensemble" }),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/não é endossado pela Riot Games/i),
    ).toBeInTheDocument();
    expect(document.documentElement.lang).toBe("pt-BR");
  });

  it("switches copy and document language to English when EN is selected", () => {
    render(<App />);

    fireEvent.click(screen.getByRole("button", { name: "EN" }));

    expect(
      screen.getByText(/Pool Ensemble isn't endorsed by Riot Games/i),
    ).toBeInTheDocument();
    expect(document.documentElement.lang).toBe("en");
  });
});
