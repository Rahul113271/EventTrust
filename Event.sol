pragma solidity >= 0.8.11 <= 0.8.11;

contract Event {
    string public users;
    string public posts;
       
    //add user details to Blockchain memory	
    function addUser(string memory us) public {
       users = us;	
    }
   //get user details
    function getUser() public view returns (string memory) {
        return users;
    }

    //add post and event detection details to Blockchain memory
    function setPost(string memory p) public {
       posts = p;	
    }

    function getPost() public view returns (string memory) {
        return posts;
    }

   constructor() public {
        users = "";
	posts="";
    }
}