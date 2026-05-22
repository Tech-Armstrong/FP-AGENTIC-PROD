/**
 * @vitest-environment jsdom
 */
import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { Header } from "../Header";

vi.mock("next/image", () => ({
  default: (props: { alt: string; src: string }) => (
    // eslint-disable-next-line @next/next/no-img-element
    <img alt={props.alt} src={props.src} data-testid="armstrong-logo" />
  ),
}));

describe("Header", () => {
  it("renders Armstrong Capital logo with correct alt text", () => {
    render(<Header />);
    const logo = screen.getByAltText("Armstrong Capital");
    expect(logo).toBeTruthy();
    expect(logo.getAttribute("src")).toContain("armstrong-capital-logo");
  });

  it("does not duplicate logo in sidebar scope", () => {
    render(<Header />);
    expect(screen.getAllByAltText("Armstrong Capital")).toHaveLength(1);
  });
});
