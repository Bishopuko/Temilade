namespace UserService.DTOs;

public class UserDto
{
    public Guid Id { get; set; }
    public string? Name { get; set; }
    public string? Email { get; set; } 
    public bool IsActive { get; set; }
    public List<PushTokenDto>? PushTokens { get; set; }
    public UserPreferenceDto? Preferences { get; set; }
    public DateTime CreatedAt { get; set; }
    public DateTime LastUpdatedAt { get; set; }
}

public class UserPreferenceDto
{
    public bool Email { get; set; }
    public bool Push { get; set; }
}

public class PushTokenDto
{
    public Guid Id { get; set; }
    public string? Token { get; set; } 
    public string? Platform { get; set; }
    public DateTime CreatedAt { get; set; }
}

public class UserContactDto
{
    public Guid UserId { get; set; }
    public string? Email { get; set; } 
    public List<PushTokenDto>? PushTokens { get; set; } 
    public UserPreferenceDto? Preferences { get; set; } 
}

public class LoginResponse
{
    public string? Token { get; set; } 
    public UserDto? User { get; set; } 
}

public class ApiResponse<T>
{
    public bool Success { get; set; }
    public T? Data { get; set; }
    public string? Error { get; set; }
    public string? Message { get; set; } 
    public PaginationMeta? Meta { get; set; }
}

public class PaginationMeta
{
    public int Total { get; set; }
    public int Limit { get; set; }
    public int Page { get; set; }
    public int TotalPages { get; set; }
    public bool HasNext { get; set; }
    public bool HasPrevious { get; set; }
}