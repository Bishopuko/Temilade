using Microsoft.AspNetCore.Mvc;
using UserService.DTOs;
using UserService.Services;

namespace UserService.Controllers;

[ApiController]
[Route("api/v1/auth")]
public class AuthController : ControllerBase
{
    private readonly IUserService _userService;
    private readonly IJwtService _jwtService;
    private readonly ILogger<AuthController> _logger;

    public AuthController(
        IUserService userService,
        IJwtService jwtService,
        ILogger<AuthController> logger)
    {
        _userService = userService;
        _jwtService = jwtService;
        _logger = logger;
    }

    [HttpPost("login")]
    public async Task<IActionResult> Login([FromBody] LoginRequest request)
    {
        _logger.LogInformation("Login attempt for email: {Email}", request.Email);

        var isValid = await _userService.ValidatePasswordAsync(request.Email!, request.Password!);
        
        if (!isValid)
        {
            return Unauthorized(new ApiResponse<object>
            {
                Success = false,
                Error = "Invalid credentials",
                Message = "Email or password is incorrect"
            });
        }

        var user = await _userService.GetUserByEmailAsync(request.Email!);
        if (user == null || !user.IsActive)
        {
            return Unauthorized(new ApiResponse<object>
            {
                Success = false,
                Error = "Invalid credentials",
                Message = "Email or password is incorrect"
            });
        }

        var token = _jwtService.GenerateToken(user.Id, user.Email ?? string.Empty);

        return Ok(new ApiResponse<LoginResponse>
        {
            Success = true,
            Data = new LoginResponse
            {
                Token = token,
                User = new UserDto
                {
                    Id = user.Id,
                    Name = user.Name ?? string.Empty,
                    Email = user.Email ?? string.Empty,
                    IsActive = user.IsActive,
                    CreatedAt = user.CreatedAt,
                    LastUpdatedAt = user.LastUpdatedAt,
                    PushTokens = user.PushTokens?.Select(t => new PushTokenDto
                    {
                        Id = t.Id,
                        Token = t.Token ?? string.Empty,
                        Platform = t.Platform,
                        CreatedAt = t.CreatedAt
                    }).ToList() ?? new(),
                    Preferences = user.UserPreference != null ? new UserPreferenceDto
                    {
                        Email = user.UserPreference.EmailEnabled,
                        Push = user.UserPreference.PushEnabled
                    } : null
                }
            },
            Message = "Login successful"
        });
    }
}