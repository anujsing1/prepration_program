package com.anuj;

import java.util.Date;

import javax.persistence.Column;
import javax.persistence.Entity;
import javax.persistence.GeneratedValue;
import javax.persistence.GenerationType;
import javax.persistence.Id;
import javax.persistence.OneToOne;
import javax.persistence.PrimaryKeyJoinColumn;
import javax.persistence.Table;

@Entity
@Table(name = "Cab_Driver")
public class CabDriver {
	private int driverId;
	private String name;
	private String licNo;
	private Date dob;
	private Date doj;
	private Taxi taxi;

	/**
	 * @return the driverId
	 */
	@Id
	@GeneratedValue(strategy = GenerationType.IDENTITY)
	@Column(name = "driver_Id", unique = true, nullable = false)
	public int getDriverId() {
		return driverId;
	}

	/**
	 * @param driverId
	 *            the driverId to set
	 */
	public void setDriverId(int driverId) {
		this.driverId = driverId;
	}

	/**
	 * @return the name
	 */
	public String getName() {
		return name;
	}

	/**
	 * @param name
	 *            the name to set
	 */
	public void setName(String name) {
		this.name = name;
	}

	/**
	 * @return the licNo
	 */
	public String getLicNo() {
		return licNo;
	}

	/**
	 * @param licNo
	 *            the licNo to set
	 */
	public void setLicNo(String licNo) {
		this.licNo = licNo;
	}

	/**
	 * @return the dob
	 */
	public Date getDob() {
		return dob;
	}

	/**
	 * @param dob
	 *            the dob to set
	 */
	public void setDob(Date dob) {
		this.dob = dob;
	}

	/**
	 * @return the doj
	 */
	public Date getDoj() {
		return doj;
	}

	/**
	 * @param doj
	 *            the doj to set
	 */
	public void setDoj(Date doj) {
		this.doj = doj;
	}

	/**
	 * @return the taxi
	 */
	@OneToOne
	@PrimaryKeyJoinColumn
	public Taxi getTaxi() {
		return taxi;
	}

	/**
	 * @param taxi
	 *            the taxi to set
	 */
	public void setTaxi(Taxi taxi) {
		this.taxi = taxi;
	}
}
