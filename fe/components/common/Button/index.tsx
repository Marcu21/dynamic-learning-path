"use client";

import { FC } from "react";
import { motion } from "framer-motion";

import { ButtonProps } from "./types";
import { baseStyles, variantStyles } from "./styles";

export const Button: FC<ButtonProps> = ({
  variant = "primary",
  children,
  className = "",
  disabled = false,
  ...motionProps
}) => (
  <motion.button
    {...motionProps}
    disabled={disabled}
    className={`${baseStyles} ${variantStyles[variant]} ${className}`}
  >
    {children}
  </motion.button>
);

export default Button;
