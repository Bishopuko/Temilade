FROM mcr.microsoft.com/dotnet/sdk:8.0 AS build
WORKDIR /src

# Copy only the project file(s) first for a proper restore layer
COPY ["UserService.csproj", "./"]
RUN dotnet restore "UserService.csproj"

# Copy rest of the files and publish (no-restore since we already restored)
COPY . .
RUN dotnet publish "UserService.csproj" -c Release -o /app/publish --no-restore /p:UseAppHost=false

FROM mcr.microsoft.com/dotnet/aspnet:8.0 AS runtime
WORKDIR /app
COPY --from=build /app/publish .
EXPOSE 8080
ENTRYPOINT ["dotnet", "UserService.dll"]