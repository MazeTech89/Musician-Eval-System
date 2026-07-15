# Registration Validation Guide

## Status: ✅ WORKING

The registration endpoint requires **strict validation** of all fields. HTTP 422 errors occur when validation rules are not met.

## Required Fields & Rules

| Field | Type | Rules | Example |
|-------|------|-------|---------|
| `username` | string | 3-50 characters | `"john_doe"` |
| `email` | string | Valid email format | `"john@example.com"` |
| `password` | string | Minimum 8 characters | `"SecurePass123!"` |
| `first_name` | string | Optional, max 100 chars | `"John"` |
| `last_name` | string | Optional, max 100 chars | `"Doe"` |
| `role` | enum | One of: admin, evaluator, musician, moderator, analyst | `"musician"` |

## Role Values (Case-Insensitive)

The API now accepts role values in **any case**:
- ✅ `"musician"` (lowercase)
- ✅ `"MUSICIAN"` (uppercase)
- ✅ `"Musician"` (mixed case)
- ✅ `"MusiciaN"` (mixed case)

Valid roles:
- `admin`
- `evaluator`
- `musician`
- `moderator`
- `analyst`

## Common 422 Errors & Solutions

### ❌ Missing Required Field
**Error**: `"Field required"` at `body.password`
**Solution**: Include all required fields: `username`, `email`, `password`, `role`

### ❌ Password Too Short
**Error**: `"String should have at least 8 characters"`
**Solution**: Use a password with 8+ characters: `"MyPassword123!"`

### ❌ Username Too Short
**Error**: `"String should have at least 3 characters"`
**Solution**: Use a username with 3+ characters: `"john_doe"` not `"jo"`

### ❌ Invalid Email Format
**Error**: `"value is not a valid email address: An email address must have an @-sign."`
**Solution**: Use a valid email: `"user@example.com"` not `"userexample.com"`

### ❌ Invalid Role Value
**Error**: `"Input should be 'admin', 'evaluator', 'musician', 'moderator' or 'analyst'"`
**Solution**: Use one of the valid roles (any case works): `"musician"` not `"invalid_role"`

## Valid Registration Request

```json
{
  "username": "john_musician",
  "email": "john@example.com",
  "password": "SecurePassword123!",
  "first_name": "John",
  "last_name": "Doe",
  "role": "musician"
}
```

**Response (201 Created)**:
```json
{
  "id": 1,
  "username": "john_musician",
  "email": "john@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "role": "musician",
  "is_active": true,
  "created_at": "2026-07-08T08:06:11.000000",
  "updated_at": "2026-07-08T08:06:11.000000",
  "last_login": null
}
```

## Frontend Implementation

```typescript
const handleRegister = async (formData: RegistrationForm) => {
  try {
    // Ensure all required fields are present
    if (!formData.username || formData.username.length < 3) {
      setError("Username must be at least 3 characters");
      return;
    }
    
    if (!formData.password || formData.password.length < 8) {
      setError("Password must be at least 8 characters");
      return;
    }
    
    if (!formData.email || !formData.email.includes("@")) {
      setError("Please enter a valid email address");
      return;
    }
    
    if (!formData.role) {
      setError("Please select a role");
      return;
    }
    
    const response = await api.post("/auth/register", {
      username: formData.username,
      email: formData.email,
      password: formData.password,
      first_name: formData.first_name || null,
      last_name: formData.last_name || null,
      role: formData.role  // Can be any case: "musician", "MUSICIAN", etc.
    });
    
    // Registration successful
    navigate("/login");
  } catch (error) {
    if (error instanceof AxiosError) {
      if (error.response?.status === 422) {
        // Validation error - check the detail field
        const validationErrors = error.response.data.detail;
        const firstError = validationErrors[0];
        setError(`${firstError.loc[1]}: ${firstError.msg}`);
      } else if (error.response?.status === 400) {
        // Business logic error (e.g., user already exists)
        setError(error.response.data.detail);
      } else {
        setError("Registration failed. Please try again.");
      }
    }
  }
};
```

## Testing

All validation rules have been tested. Run tests with:

```bash
python test_validation_errors.py
```

This tests all possible validation scenarios:
- Missing fields
- Invalid field lengths
- Invalid email formats
- Invalid role values
- All case variations for roles

## Summary

✅ **Rate limiting**: Implemented (5/minute on registration endpoint)
✅ **Role case normalization**: Working (accepts any case)
✅ **Validation**: Strict but clear error messages
✅ **Backend**: Running and operational
