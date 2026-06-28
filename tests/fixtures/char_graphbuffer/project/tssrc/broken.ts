/** Intentionally contains a syntax error to exercise error-node recovery (#94/#99).
 * The valid symbols above/below the error must still be recovered.
 */

export function before(): string {
  return "ok";
}

export class Broken {
  doThing( {
    // ^ missing closing paren / param list — introduces an ERROR node
    return 1;
  }
}

export function after(): number {
  return 42;
}
