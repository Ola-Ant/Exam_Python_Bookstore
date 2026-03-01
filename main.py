import cli

def main():
    try:
        cli.main_menu()

    except KeyboardInterrupt:
        print("\n\nПрограму зупинено користувачем")
    except Exception as e:
        print(f"\nКритична помилка при запуску: {e}")
    finally:
        print("\nРоботу з системою завершено")

if __name__ == "__main__":
    main()