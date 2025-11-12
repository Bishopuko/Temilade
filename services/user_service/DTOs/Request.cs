namespace UserService.DTOs;

public class CreateUserRequest
{
    public string? Name { get; set; }

    public string? Email { get; set; }

    public string? Password { get; set; }
    public string? PushToken { get; set; }

    public UserPreferenceDto? Preferences { get; set; }
}

public class UpdateUserRequest
{
    public string? Name { get; set; }

    public string? Email { get; set; }
}

public class UpdatePreferencesRequest
{
    public bool Email { get; set; }

    public bool Push { get; set; }
}

public class AddPushTokenRequest
{
    public string? PushToken { get; set; }

    public string? Platform { get; set; }
}

public class LoginRequest
{
    public string? Email { get; set; }

    public string? Password { get; set; }
}