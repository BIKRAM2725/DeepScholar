declare global {
  namespace Express {
    interface Request {
      user?: {
        sub: string;          // user id
        iss: string;          // issuer
        exp: number;          // expiry
        iat: number;          // issued at
        azp?: string;         // authorized party
        sid?: string;         // session id
        [key: string]: any;   // allow extra claims
      };
    }
  }
}

export {};