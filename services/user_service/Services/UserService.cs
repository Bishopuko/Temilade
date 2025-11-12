using Microsoft.EntityFrameworkCore;
using UserService.Data;
using UserService.DTOs;
using UserService.Models;
using BCrypt.Net;



namespace UserService.Services;

public interface IUserService
{
    Task<(User? user, string? error)> CreateUserAsync(CreateUserRequest request);
    Task<User?> GetUserByIdAsync(Guid id);
    Task<User?> GetUserByEmailAsync(string email);
    Task<(bool success, string? error)> UpdateUserAsync(Guid id, UpdateUserRequest request);
    Task<(bool success, string? error)> UpdatePreferencesAsync(Guid id, UpdatePreferencesRequest request);
    Task<(bool success, string? error)> AddPushTokenAsync(Guid id, AddPushTokenRequest request);
    Task<UserContactDto?> GetUserContactAsync(Guid id);
    Task<(List<User> users, int total)> GetUsersAsync(int page, int limit);
    Task<bool> ValidatePasswordAsync(string email, string password);
}

public class UserServiceImpl : IUserService
{
    private readonly AppDbContext _context;
    private readonly IRedisCacheService _cache;
    private readonly ILogger<UserServiceImpl> _logger;

    public UserServiceImpl(AppDbContext context, IRedisCacheService cache, ILogger<UserServiceImpl> logger)
    {
        _context = context;
        _cache = cache;
        _logger = logger;
    }

    public async Task<(User? user, string? error)> CreateUserAsync(CreateUserRequest request)
    {
        try
        {
            if (await _context.Users!.AnyAsync(u => u.Email == request.Email))
                return (null, "User with this email already exists");

            var user = new User
            {
                Id = Guid.NewGuid(),
                Name = request.Name,
                Email = request.Email,
                PasswordHash = BCrypt.Net.BCrypt.HashPassword(request.Password),
                IsActive = true,
                CreatedAt = DateTime.UtcNow
            };

            _context.Users!.Add(user);

            var preference = new UserPreference
            {
                Id = Guid.NewGuid(),
                UserId = user.Id,
                EmailEnabled = request.Preferences?.Email ?? true,
                PushEnabled = request.Preferences?.Push ?? true,
                CreatedAt = DateTime.UtcNow
            };

            _context.UserPreferences!.Add(preference);

            if (!string.IsNullOrWhiteSpace(request.PushToken))
            {
                _context.PushTokens!.Add(new PushToken
                {
                    Id = Guid.NewGuid(),
                    UserId = user.Id,
                    Token = request.PushToken,
                    Platform = "unknown",
                    CreatedAt = DateTime.UtcNow
                });
            }

            await _context.SaveChangesAsync();

            await CacheUserPreferencesAsync(user.Id, preference);
            return (user, null);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error creating user");
            return (null, "Internal server error while creating user");
        }
    }

    public async Task<User?> GetUserByIdAsync(Guid id) =>
        await _context.Users!
            .Include(u => u.UserPreference)
            .Include(u => u.PushTokens)
            .FirstOrDefaultAsync(u => u.Id == id);

    public async Task<User?> GetUserByEmailAsync(string email) =>
        await _context.Users!
            .Include(u => u.UserPreference)
            .Include(u => u.PushTokens)
            .FirstOrDefaultAsync(u => u.Email == email);

    public async Task<(bool success, string? error)> UpdateUserAsync(Guid id, UpdateUserRequest request)
    {
        try
        {
            var user = await _context.Users!.FindAsync(id);
            if (user == null) return (false, "User not found");

            if (!string.IsNullOrWhiteSpace(request.Name))
                user.Name = request.Name;

            if (!string.IsNullOrWhiteSpace(request.Email))
            {
                if (await _context.Users.AnyAsync(u => u.Email == request.Email && u.Id != id))
                    return (false, "Email already in use");

                user.Email = request.Email;
            }

            user.LastUpdatedAt = DateTime.UtcNow;
            await _context.SaveChangesAsync();
            return (true, null);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error updating user");
            return (false, "Internal server error while updating user");
        }
    }

    public async Task<(bool success, string? error)> UpdatePreferencesAsync(Guid id, UpdatePreferencesRequest request)
    {
        try
        {
            var preference = await _context.UserPreferences!.FirstOrDefaultAsync(p => p.UserId == id);

            if (preference == null)
            {
                preference = new UserPreference
                {
                    Id = Guid.NewGuid(),
                    UserId = id,
                    EmailEnabled = request.Email,
                    PushEnabled = request.Push,
                    CreatedAt = DateTime.UtcNow
                };

                _context.UserPreferences!.Add(preference);
            }
            else
            {
                preference.EmailEnabled = request.Email;
                preference.PushEnabled = request.Push;
                preference.LastUpdatedAt = DateTime.UtcNow;
            }

            await _context.SaveChangesAsync();
            await CacheUserPreferencesAsync(id, preference);
            return (true, null);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error updating preferences");
            return (false, "Internal server error while updating preferences");
        }
    }

    public async Task<(bool success, string? error)> AddPushTokenAsync(Guid id, AddPushTokenRequest request)
    {
        try
        {
            if (await _context.Users!.FindAsync(id) == null)
                return (false, "User not found");

            var token = await _context.PushTokens!
                .FirstOrDefaultAsync(t => t.UserId == id && t.Token == request.PushToken);

            if (token == null)
            {
                _context.PushTokens!.Add(new PushToken
                {
                    Id = Guid.NewGuid(),
                    UserId = id,
                    Token = request.PushToken,
                    Platform = request.Platform ?? "unknown",
                    CreatedAt = DateTime.UtcNow
                });
            }
            else
            {
                token.Platform = request.Platform ?? token.Platform;
                token.CreatedAt = DateTime.UtcNow;
            }

            await _context.SaveChangesAsync();
            await _cache.RemoveAsync($"user:contact:{id}");

            return (true, null);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error adding push token");
            return (false, "Internal server error while adding push token");
        }
    }

    public async Task<UserContactDto?> GetUserContactAsync(Guid id)
    {
        var key = $"user:contact:{id}";
        var cached = await _cache.GetAsync<UserContactDto>(key);
        if (cached != null) return cached;

        var user = await GetUserByIdAsync(id);
        if (user == null) return null;

        var dto = new UserContactDto
        {
            UserId = user.Id,
            Email = user.Email ?? "",
            Preferences = new UserPreferenceDto
            {
                Email = user.UserPreference?.EmailEnabled ?? true,
                Push = user.UserPreference?.PushEnabled ?? true
            },
            PushTokens = user.PushTokens!.Select(t => new PushTokenDto
            {
                Id = t.Id,
                Token = t.Token,
                Platform = t.Platform,
                CreatedAt = t.CreatedAt
            }).ToList()
        };

        await _cache.SetAsync(key, dto, TimeSpan.FromMinutes(5));
        return dto;
    }

    public async Task<(List<User> users, int total)> GetUsersAsync(int page, int limit)
    {
        var query = _context.Users!
            .Include(u => u.UserPreference)
            .Include(u => u.PushTokens);

        var total = await query.CountAsync();
        var users = await query
            .OrderByDescending(u => u.CreatedAt)
            .Skip((page - 1) * limit)
            .Take(limit)
            .ToListAsync();

        return (users, total);
    }

    public async Task<bool> ValidatePasswordAsync(string email, string password)
    {
        var user = await _context.Users!.FirstOrDefaultAsync(u => u.Email == email);
        return user != null && BCrypt.Net.BCrypt.Verify(password, user.PasswordHash);
    }

    private Task CacheUserPreferencesAsync(Guid userId, UserPreference p) =>
        _cache.SetAsync($"user:preferences:{userId}", new UserPreferenceDto
        {
            Email = p.EmailEnabled,
            Push = p.PushEnabled
        }, TimeSpan.FromMinutes(10));
}
