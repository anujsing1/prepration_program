package com.groupon;

import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.Date;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

public class Employee {
	private int id;
	private String firstName;
	private String lastName;
	private Date dob;
	public Employee(int id, String firstName, String lastName) {
		this.id=id;
		this.firstName=firstName;
		this.lastName=lastName;
	}
	
	/*public int compareTo(Employee e)
	{
		return this.id-e.id;
	}*/
	
	public static final Comparator<Employee> byFLName = new Comparator<Employee>(){
		public int compare(Employee e1, Employee e2){
			int n = e1.firstName.compareToIgnoreCase(e2.firstName);
			if(0 != n)
				return n;
			n = e1.lastName.compareToIgnoreCase(e2.lastName);
			return n;
		}
	};
	
	/**
	 * @return the id
	 */
	public int getId() {
		return id;
	}
	/**
	 * @param id the id to set
	 */
	public void setId(int id) {
		this.id = id;
	}
	/**
	 * @return the firstName
	 */
	public String getFirstName() {
		return firstName;
	}
	/**
	 * @param firstName the firstName to set
	 */
	public void setFirstName(String firstName) {
		this.firstName = firstName;
	}
	/**
	 * @return the lastName
	 */
	public String getLastName() {
		return lastName;
	}
	/**
	 * @param lastName the lastName to set
	 */
	public void setLastName(String lastName) {
		this.lastName = lastName;
	}
	/**
	 * @return the dob
	 */
	public Date getDob() {
		return dob;
	}
	/**
	 * @param dob the dob to set
	 */
	public void setDob(Date dob) {
		this.dob = dob;
	}
	
	@Override
	public String toString() {
		return "id: "+id+", FirstName : " + firstName + ", Last Name : " + lastName;
	}
	
	public static void main(String[] args) {
		
		Map<Integer, Employee> empMap = new HashMap<Integer, Employee>(); 
		
		List<Employee> list = new ArrayList<Employee>();
		Employee e1 = new Employee(1 , "A", "B");
		list.add(e1);
		Employee e2 = new Employee(2 , "A", "A");
		list.add(e2);
		Employee e3 = new Employee(3 , "B", "C");
		list.add(e3);
		Employee e4 = new Employee(4 , "B", "B");
		list.add(e4);
		Employee e5 = new Employee(5 , "B", "A");
		list.add(e5);
		
		empMap.put(e1.id, e1);
		empMap.put(e2.id, e2);
		empMap.put(e3.id, e3);
		
		for (Integer id : empMap.keySet())
		{
			Employee emp = empMap.get(id);
			System.out.println(emp.toString());
		}
		
	/*	Collections.sort(list, byFLName);
		
		for (Employee e : list)
		{
			System.out.println(e.toString());
		}
		Collections.sort(list);
		
		for (Employee e : list)
		{
			System.out.println(e.toString());
		}*/
	}
	
}
