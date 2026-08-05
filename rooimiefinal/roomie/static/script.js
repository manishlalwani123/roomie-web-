// script.js

document.addEventListener('DOMContentLoaded', function () {
    // Get the container where user profiles will be added
    var userProfileContainer = document.getElementById('user-profiles');

    // Example data (replace this with actual data from your Flask app)
    var userProfiles = [
        { id: 1, name: 'John Doe', age: 25, department: 'Computer Science' },
        { id: 2, name: 'Jane Smith', age: 22, department: 'Electrical Engineering' }
        // Add more user profiles here as needed
    ];

    // Loop through each user profile and create HTML elements to display them
    userProfiles.forEach(function (profile) {
        // Create profile container
        var profileContainer = document.createElement('div');
        profileContainer.classList.add('user-profile');

        // Create profile image
        var profileImage = document.createElement('div');
        profileImage.classList.add('profile-image');
        profileImage.innerHTML = '<img src="profile-placeholder.png" alt="Profile Image">'; // Replace profile-placeholder.png with actual image URL
        profileContainer.appendChild(profileImage);

        // Create profile details
        var profileDetails = document.createElement('div');
        profileDetails.classList.add('profile-details');
        profileDetails.innerHTML = '<h2>' + profile.name + '</h2>' +
                                    '<p>Age: ' + profile.age + '</p>' +
                                    '<p>Department: ' + profile.department + '</p>';
        profileContainer.appendChild(profileDetails);

        // Append profile container to the user profile container
        userProfileContainer.appendChild(profileContainer);
    });
});
