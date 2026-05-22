/**
 * @vitest-environment jsdom
 */
import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { Header } from "../Header";
import { ThemeProvider } from "../providers/ThemeProvider";

vi.mock("next/image", () => ({
  default: (props: { alt: string; src: string }) => (
    // eslint-disable-next-line @next/next/no-img-element
    <img alt={props.alt} src={props.src} data-testid="armstrong-logo" />
  ),
}));

function renderHeader() {
  return render(
    <ThemeProvider>
      <Header />
    </ThemeProvider>,
  );
}

describe("Header", () => {
  it("renders Armstrong Capital logo with correct alt text", () => {
    renderHeader();
    const logo = screen.getByAltText("Armstrong Capital");
    expect(logo).toBeTruthy();
    expect(logo.getAttribute("src")).toContain("armstrong-capital-logo");
  });

  it("renders theme toggle", () => {
    renderHeader();
    expect(screen.getByRole("button", { name: /toggle theme|switch to/i })).toBeTruthy();
  });
});
