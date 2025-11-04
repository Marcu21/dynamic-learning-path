export const baseStyles =
  "inline-flex items-center justify-center gap-2 px-4 py-2 rounded-lg font-bold transition focus:outline-none disabled:opacity-50 disabled:cursor-not-allowed whitespace-nowrap";

export const variantStyles: Record<
  NonNullable<string>,
  string
> = {
  primary:
    "bg-primary text-white hover:bg-primary-dark focus:ring-2 focus:ring-primary",
  secondary:
    "bg-secondary text-white hover:bg-secondary-dark focus:ring-2 focus:ring-secondary",
  alert:
    "bg-alert text-white hover:bg-alert-dark focus:ring-2 focus:ring-alert",
  success:
    "bg-success text-white hover:bg-success-dark focus:ring-2 focus:ring-success",
  warning:
    "bg-warning text-white hover:bg-warning-dark focus:ring-2 focus:ring-warning",
  hollow:
    "border border-primary text-primary hover:bg-primary-light focus:ring-2 focus:ring-primary",
  accent:
    "bg-accent text-white hover:bg-accent-dark focus:ring-2 focus:ring-accent",
};
