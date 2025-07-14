import {
  Box,
  Flex,
  Button,
  useColorMode,
  IconButton,
  Menu,
  MenuButton,
  MenuList,
  MenuItem,
} from "@chakra-ui/react";
import { HamburgerIcon, MoonIcon, SunIcon } from "@chakra-ui/icons";
import { Link, useNavigate } from "react-router-dom";
import useAuthStore from "../store/authStore";

function Layout({ children }) {
  const { colorMode, toggleColorMode } = useColorMode();
  const navigate = useNavigate();
  const { user, logout } = useAuthStore();

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <Box>
      <Flex
        as="nav"
        align="center"
        justify="space-between"
        wrap="wrap"
        padding="1.5rem"
        bg={colorMode === "light" ? "white" : "gray.800"}
        color={colorMode === "light" ? "gray.800" : "white"}
        borderBottom="1px"
        borderColor={colorMode === "light" ? "gray.200" : "gray.700"}
      >
        <Flex align="center" mr={5}>
          <Link to="/">
            <Box fontSize="xl" fontWeight="bold">
              KnowFlow
            </Box>
          </Link>
        </Flex>

        <Flex align="center" gap={4}>
          <Link to="/">
            <Button variant="ghost">Chat</Button>
          </Link>
          <Link to="/documents">
            <Button variant="ghost">Documents</Button>
          </Link>
          <IconButton
            icon={colorMode === "light" ? <MoonIcon /> : <SunIcon />}
            onClick={toggleColorMode}
            variant="ghost"
            aria-label="Toggle color mode"
          />
          <Menu>
            <MenuButton
              as={IconButton}
              icon={<HamburgerIcon />}
              variant="ghost"
              aria-label="Options"
            />
            <MenuList>
              <MenuItem onClick={handleLogout}>Logout</MenuItem>
            </MenuList>
          </Menu>
        </Flex>
      </Flex>

      <Box p={4}>{children}</Box>
    </Box>
  );
}

export default Layout;
