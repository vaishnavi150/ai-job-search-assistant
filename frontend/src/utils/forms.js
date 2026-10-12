// Wraps a field's setter so editing it clears the errors shown for it on the
// last submit; otherwise "Passwords don't match" lingers after they do match.
export function clearOnEdit(setValue, setErrors, ...keys) {
  return (value) => {
    setValue(value);
    setErrors((errs) => (keys.some((k) => errs[k]) ? { ...errs, ...Object.fromEntries(keys.map((k) => [k, ''])) } : errs));
  };
}
