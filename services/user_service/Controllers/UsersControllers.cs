using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using System.Security.Claims;
using UserService.DTOs;
using UserService.Services;

namespace UserService.Controllers;

[ApiController]
[Route("api/v1/users")]
public class UsersController : ControllerBase
{
    private readonly IUserService _userService;
    private readonly ILogger<UsersController> _logger;

    public UsersController(IUserService userService, ILogger<UsersController> logger)
    {
        _userService = userService;
        _logger = logger;
    }

    [HttpPost]
    public async Task<IActionResult> CreateUser([FromBody] CreateUserRequest request)
    {
        _logger.LogInformation("Creating user with email: {Email}", request.Email);

        var (user, error) = await _userService.CreateUserAsync(request);
        
        if (user == null)
        {
            return BadRequest(new ApiResponse<object>
            {
                Success = false,
                Error = error,
                Message = "Failed to create user"
            });
        }

        var userDto = MapToDto(user);

        return CreatedAtAction(
            nameof(GetUser),
            new { id = user.Id },
            new ApiResponse<UserDto>
            {
                Success = true,
                Data = userDto,
                Message = "User created successfully"
            });
    }

    [HttpGet("{id:guid}")]
    [Authorize]
    public async Task<IActionResult> GetUser(Guid id)
    {
        var user = await _userService.GetUserByIdAsync(id);
        
        if (user == null)
        {
            return NotFound(new ApiResponse<object>
            {
                Success = false,
                Error = "User not found",
                Message = "User does not exist"
            });
        }

        return Ok(new ApiResponse<UserDto>
        {
            Success = true,
            Data = MapToDto(user),
            Message = "User retrieved successfully"
        });
    }

    [HttpGet]
    [Authorize]
    public async Task<IActionResult> GetUsers([FromQuery] int page = 1, [FromQuery] int limit = 10)
    {
        if (page < 1) page = 1;
        if (limit < 1) limit = 10;
        if (limit > 100) limit = 100;

        var (users, total) = await _userService.GetUsersAsync(page, limit);
        var userDtos = users.Select(MapToDto).ToList();

        var totalPages = (int)Math.Ceiling(total / (double)limit);

        return Ok(new ApiResponse<List<UserDto>>
        {
            Success = true,
            Data = userDtos,
            Message = "Users retrieved successfully",
            Meta = new PaginationMeta
            {
                Total = total,
                Limit = limit,
                Page = page,
                TotalPages = totalPages,
                HasNext = page < totalPages,
                HasPrevious = page > 1
            }
        });
    }

    [HttpPut("{id:guid}")]
    [Authorize]
    public async Task<IActionResult> UpdateUser(Guid id, [FromBody] UpdateUserRequest request)
    {
        var currentUserId = GetCurrentUserId();
        if (currentUserId != id)
        {
            return Forbid();
        }

        var (success, error) = await _userService.UpdateUserAsync(id, request);
        
        if (!success)
        {
            return BadRequest(new ApiResponse<object>
            {
                Success = false,
                Error = error,
                Message = "Failed to update user"
            });
        }

        return Ok(new ApiResponse<object>
        {
            Success = true,
            Message = "User updated successfully"
        });
    }

    [HttpPut("{id:guid}/preferences")]
    [Authorize]
    public async Task<IActionResult> UpdatePreferences(Guid id, [FromBody] UpdatePreferencesRequest request)
    {
        var currentUserId = GetCurrentUserId();
        if (currentUserId != id)
        {
            return Forbid();
        }

        var (success, error) = await _userService.UpdatePreferencesAsync(id, request);
        
        if (!success)
        {
            return BadRequest(new ApiResponse<object>
            {
                Success = false,
                Error = error,
                Message = "Failed to update preferences"
            });
        }

        return Ok(new ApiResponse<object>
        {
            Success = true,
            Message = "Preferences updated successfully"
        });
    }

    [HttpPost("{id:guid}/tokens")]
    [Authorize]
    public async Task<IActionResult> AddPushToken(Guid id, [FromBody] AddPushTokenRequest request)
    {
        var currentUserId = GetCurrentUserId();
        if (currentUserId != id)
        {
            return Forbid();
        }

        var (success, error) = await _userService.AddPushTokenAsync(id, request);
        
        if (!success)
        {
            return BadRequest(new ApiResponse<object>
            {
                Success = false,
                Error = error,
                Message = "Failed to add push token"
            });
        }

        return Ok(new ApiResponse<object>
        {
            Success = true,
            Message = "Push token added successfully"
        });
    }

    [HttpGet("{id:guid}/contact")]
    [Authorize]
    public async Task<IActionResult> GetUserContact(Guid id)
    {
        var contact = await _userService.GetUserContactAsync(id);
        
        if (contact == null)
        {
            return NotFound(new ApiResponse<object>
            {
                Success = false,
                Error = "User not found",
                Message = "User contact information not available"
            });
        }

        return Ok(new ApiResponse<UserContactDto>
        {
            Success = true,
            Data = contact,
            Message = "User contact retrieved successfully"
        });
    }

    private Guid GetCurrentUserId()
    {
        var userIdClaim = User.FindFirst(ClaimTypes.NameIdentifier)?.Value;
        return Guid.TryParse(userIdClaim, out var userId) ? userId : Guid.Empty;
    }

    private static UserDto MapToDto(Models.User user)
    {
        return new UserDto
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
        };
    }
}